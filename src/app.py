"""
Flask 主应用
处理飞书 webhook：事件订阅验证、消息接收、调用图片生成服务、回复用户
"""
import json
import logging
import os
import re
import tempfile
import threading
import time
from pathlib import Path
from http import HTTPStatus

from flask import Flask, jsonify, request

from config import Config
from feishu_api import feishu_api
from image_gen import get_image_generator
from utils import (
    acquire_generation_lock,
    detect_media_type,
    init_logging,
    is_duplicate_message,
    parse_size_or_ratio,
    postprocess_image,
    release_generation_lock,
)
from video_gen import get_video_generator


def _safe_text_content(text: str) -> str:
    """安全构造飞书 text 消息的 content JSON"""
    return json.dumps({"text": text}, ensure_ascii=False)


def _safe_image_content(image_key: str) -> str:
    """安全构造飞书 image 消息的 content JSON"""
    return json.dumps({"image_key": image_key}, ensure_ascii=False)

logger = logging.getLogger(__name__)

_reference_lock = threading.Lock()
_recent_reference_images: dict[str, dict] = {}


def cache_reference_image(chat_id: str, image_path: str, message_id: str = "", ttl_seconds: int | None = None) -> None:
    """缓存某个群/会话最近一张参考图（文件系统+内存双写，兼容多 worker）。"""
    meta = {
        "path": image_path,
        "message_id": message_id,
        "timestamp": time.time(),
        "ttl": ttl_seconds or Config.REFERENCE_IMAGE_TTL_SECONDS,
    }
    # 内存缓存（本 worker 快速读取）
    with _reference_lock:
        _recent_reference_images[chat_id] = meta
    # 文件系统缓存（跨 worker 共享）
    try:
        ref_dir = Path(Config.REFERENCE_IMAGE_DIR)
        ref_dir.mkdir(parents=True, exist_ok=True)
        (ref_dir / f"ref_meta_{chat_id}.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
    except Exception:
        pass


def get_recent_reference_image(chat_id: str, ttl_seconds: int | None = None) -> str | None:
    """获取某个群/会话仍有效的最近参考图路径（先读内存，再读文件系统）。"""
    # 1. 先尝试内存缓存（本 worker）
    with _reference_lock:
        item = _recent_reference_images.get(chat_id)
        if item:
            ttl = ttl_seconds or item.get("ttl") or Config.REFERENCE_IMAGE_TTL_SECONDS
            path = item.get("path")
            if time.time() - item.get("timestamp", 0) <= ttl and path and os.path.exists(path):
                return path
            _recent_reference_images.pop(chat_id, None)

    # 2. 回退到文件系统缓存（其他 worker 写入）
    try:
        ref_dir = Path(Config.REFERENCE_IMAGE_DIR)
        meta_path = ref_dir / f"ref_meta_{chat_id}.json"
        if not meta_path.exists():
            return None
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        ttl = ttl_seconds or meta.get("ttl") or Config.REFERENCE_IMAGE_TTL_SECONDS
        path = meta.get("path")
        if time.time() - meta.get("timestamp", 0) > ttl or not path or not os.path.exists(path):
            meta_path.unlink(missing_ok=True)
            return None
        # 同步到内存
        with _reference_lock:
            _recent_reference_images[chat_id] = meta
        return path
    except Exception:
        return None


def _extract_image_key(content: dict) -> str:
    """从飞书 image 消息 content 中提取 image_key/file_key。"""
    return content.get("image_key") or content.get("file_key") or content.get("key") or ""


def _handle_reference_image_message(chat_id: str, message_id: str, image_key: str) -> None:
    """下载并缓存用户发来的图片，作为后续图生图参考图。"""
    try:
        if not image_key:
            feishu_api.reply_message(message_id, "text", _safe_text_content("没识别到图片资源 key，请再发一次图片～"))
            return
        image_data = feishu_api.download_message_resource(message_id, image_key, "image")
        ref_dir = Path(Config.REFERENCE_IMAGE_DIR)
        ref_dir.mkdir(parents=True, exist_ok=True)
        ext = ".png"
        if image_data.startswith(b"\xff\xd8\xff"):
            ext = ".jpg"
        elif image_data.startswith(b"RIFF"):
            ext = ".webp"
        image_path = ref_dir / f"ref_{chat_id}_{int(time.time())}{ext}"
        image_path.write_bytes(image_data)
        cache_reference_image(chat_id, str(image_path), message_id=message_id)
        logger.info("已缓存参考图: chat=%s path=%s size=%s", chat_id, image_path, len(image_data))
        feishu_api.reply_message(message_id, "text", _safe_text_content("收到参考图啦～你再发一句想怎么改，我就按这张图生成 🐣"))
    except Exception as e:
        logger.exception("缓存参考图失败: %s", e)
        try:
            feishu_api.reply_message(message_id, "text", _safe_text_content(f"参考图读取失败：{str(e)[:200]}"))
        except Exception:
            pass


def create_app() -> Flask:
    init_logging(Config.LOG_LEVEL)
    app = Flask(__name__)

    # 检查配置
    missing = Config.validate()
    if missing:
        logger.warning(f"配置缺失: {missing}")
    else:
        logger.info("配置检查通过")

    @app.route("/webhook", methods=["POST"])
    def webhook():
        """飞书事件订阅入口"""
        data = request.get_json(silent=True) or {}
        logger.debug(f"收到请求: {json.dumps(data, ensure_ascii=False)[:500]}")

        # 1. URL 验证（首次配置事件订阅时飞书会发送 challenge）
        if "challenge" in data:
            return jsonify({"challenge": data["challenge"]}), HTTPStatus.OK

        # 2. 处理事件回调
        header = data.get("header", {})
        event_type = header.get("event_type", "")

        if event_type == "im.message.receive_v1":
            event = data.get("event", {})
            message = event.get("message", {})
            sender = event.get("sender", {}).get("sender_id", {}).get("open_id", "")
            msg_type = message.get("message_type", "")
            content_raw = message.get("content", "{}")
            message_id = message.get("message_id", "")
            chat_id = message.get("chat_id", "")

            # 消息去重
            if is_duplicate_message(message_id):
                logger.info(f"消息已处理过，跳过: {message_id}")
                return "", HTTPStatus.OK

            try:
                content = json.loads(content_raw)
            except json.JSONDecodeError:
                logger.warning(f"无法解析消息内容: {content_raw}")
                return "", HTTPStatus.OK

            if msg_type == "image":
                image_key = _extract_image_key(content)
                logger.info(f"收到参考图 from {sender}: key={image_key[:12]}...")
                threading.Thread(
                    target=_handle_reference_image_message,
                    args=(chat_id, message_id, image_key),
                    daemon=True,
                ).start()
                return "", HTTPStatus.OK

            # 只处理文本和图片消息
            if msg_type != "text":
                return "", HTTPStatus.OK

            text = content.get("text", "").strip()

            # 过滤掉 @机器人 的前缀
            text = re.sub(r"<at[^>]*>.*?</at>", "", text).strip()

            if not text:
                return "", HTTPStatus.OK

            logger.info(f"收到消息 from {sender}: {text[:80]}")

            # 判断是图片还是视频请求
            media_type = detect_media_type(text)

            # 异步处理，避免 webhook 超时
            def process_async():
                try:
                    if media_type == "video":
                        _handle_video_request(chat_id, message_id, text)
                    else:
                        reference_path = get_recent_reference_image(chat_id)
                        _handle_image_request(chat_id, message_id, text, reference_images=[reference_path] if reference_path else None)
                except Exception as e:
                    logger.exception(f"处理请求失败: {e}")
                    try:
                        feishu_api.reply_message(
                            message_id, "text",
                            _safe_text_content("抱歉，处理出错了，请稍后重试。")
                        )
                    except Exception:
                        pass

            threading.Thread(target=process_async, daemon=True).start()

        return "", HTTPStatus.OK

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), HTTPStatus.OK

    return app


def _handle_image_request(chat_id: str, message_id: str, text: str, reference_images: list[str] | None = None) -> None:
    """处理图片生成请求。若 reference_images 存在，则走图生图。"""
    # 1. 获取全局锁
    if not acquire_generation_lock():
        feishu_api.reply_message(
            message_id, "text",
            _safe_text_content("上一个生成任务还在跑，请稍后再发。")
        )
        return

    try:
        # 2. 解析尺寸/比例
        size_info = parse_size_or_ratio(text)
        aspect_ratio = size_info["aspect_ratio"]
        target_size = size_info.get("target_size")
        raw_size_text = size_info.get("raw_size_text", "")

        logger.info(f"[Handler] 解析到比例={aspect_ratio}, 尺寸={target_size}, 原始文本={raw_size_text}")

        # 3. 先回复正在生成
        size_display = f"{target_size[0]}x{target_size[1]}" if target_size else aspect_ratio
        ref_hint = "，已带参考图" if reference_images else ""
        feishu_api.reply_message(
            message_id, "text",
            _safe_text_content(f"🎨 正在生成图片（{size_display}{ref_hint}），请稍候...")
        )

        # 4. 调用图片生成服务
        generator = get_image_generator()
        result = generator.generate(
            prompt=text,
            aspect_ratio=aspect_ratio,
            target_size=target_size,
            reference_images=reference_images,
        )

        if not result["success"]:
            error_msg = result.get("error", "未知错误")
            feishu_api.reply_message(
                message_id, "text",
                _safe_text_content(f"生成失败：{error_msg}")
            )
            return

        image_path = result["image_path"]
        tool_used = result.get("tool_used", "unknown")

        # 5. 后处理（自定义尺寸）
        final_path = image_path
        if target_size and Config.ENABLE_CUSTOM_SIZE_POSTPROCESS:
            try:
                ext = os.path.splitext(image_path)[1] or ".png"
                tmp_dir = tempfile.gettempdir()
                final_name = f"processed_{os.path.basename(image_path)}"
                final_path = os.path.join(tmp_dir, final_name)
                postprocess_image(image_path, target_size, final_path)
                logger.info(f"[Handler] 后处理完成: {final_path}")
            except Exception as e:
                logger.warning(f"[Handler] 后处理失败，使用原图: {e}")
                final_path = image_path

        # 6. 读取图片并上传到飞书
        with open(final_path, "rb") as f:
            image_data = f.read()

        image_key = feishu_api.upload_image(image_data)

        # 7. 回复图片
        feishu_api.reply_message(
            message_id, "image",
            _safe_image_content(image_key)
        )

        # 8. 回复文字信息
        final_size_text = raw_size_text if raw_size_text else aspect_ratio
        if target_size:
            final_size_text = f"{target_size[0]}x{target_size[1]}"

        feishu_api.reply_message(
            message_id, "text",
            _safe_text_content(f"已生成，模型/工具：{tool_used}，尺寸：{final_size_text}")
        )

        logger.info(f"[Handler] 图片生成完成并回复用户")

    finally:
        release_generation_lock()


def _handle_video_request(chat_id: str, message_id: str, text: str) -> None:
    """处理视频生成请求（v1.0 占位）"""
    if not acquire_generation_lock():
        feishu_api.reply_message(
            message_id, "text",
            _safe_text_content("上一个生成任务还在跑，请稍后再发。")
        )
        return

    try:
        feishu_api.reply_message(
            message_id, "text",
            _safe_text_content("当前 gpt-image-2-medium 是图片模型，不能直接生成视频。视频需要接入 Veo / 可灵 / Runway / Sora / Seedance 等视频模型。")
        )
    finally:
        release_generation_lock()
