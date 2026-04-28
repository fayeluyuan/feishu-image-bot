"""
工具函数
"""
import logging
import os
import re
import threading
import time
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)

# 简单的消息去重缓存（message_id -> timestamp）
# 保留最近 10 分钟的消息
_processed_messages: dict[str, float] = {}
_lock = threading.Lock()
_CACHE_TTL = 600  # 10 分钟

# 全局生成锁
_generation_lock = threading.Lock()
_generation_in_progress = False


def init_logging(level: str = "INFO") -> None:
    """初始化日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def is_duplicate_message(message_id: str) -> bool:
    """
    检查消息是否已处理过（防止飞书重复推送）
    返回 True 表示已处理，应跳过
    """
    with _lock:
        now = time.time()
        # 清理过期缓存
        expired = [k for k, v in _processed_messages.items() if now - v > _CACHE_TTL]
        for k in expired:
            del _processed_messages[k]

        if message_id in _processed_messages:
            return True
        _processed_messages[message_id] = now
        return False


def detect_media_type(text: str) -> str:
    """
    根据用户输入判断是图片还是视频请求
    返回: 'image' | 'video' | 'unknown'
    """
    text_lower = text.lower()
    video_keywords = [
        "视频", "video", "生成视频", "做视频", "拍视频",
        "video生成", "生成video", "动图", "动画",
    ]
    image_keywords = [
        "图片", "image", "照片", "图", "画", "生成图片",
        "做图", "画图", "picture", "photo",
    ]

    for kw in video_keywords:
        if kw in text_lower:
            return "video"
    for kw in image_keywords:
        if kw in text_lower:
            return "image"

    # 默认当图片处理
    return "image"


def parse_size_or_ratio(text: str) -> dict:
    """
    解析用户输入中的尺寸/比例信息

    支持识别：
    - 1024x1536 / 1024*1536 / 1024×1536
    - 1536x1024
    - 750x1200
    - 7501500（纯数字组合）
    - 9:16 / 16:9 / 1:1
    - 竖版 / 横版 / 方图
    - PPT / 淘宝详情页 / 电商长图 / 小红书 / 抖音 / 视频号

    返回:
    {
        "aspect_ratio": "portrait/landscape/square/custom",
        "target_size": [width, height] 或 None,
        "raw_size_text": 原始匹配到的尺寸文本
    }
    """
    result = {
        "aspect_ratio": "portrait",
        "target_size": None,
        "raw_size_text": "",
    }

    t = text.strip().lower()

    # 1. 检测明确的数字尺寸（带分隔符）
    # 匹配 1024x1536, 1024*1536, 1024×1536
    size_match = re.search(r"(\d{2,4})[x×*](\d{2,4})", t)
    if size_match:
        w = int(size_match.group(1))
        h = int(size_match.group(2))
        result["target_size"] = [w, h]
        result["raw_size_text"] = size_match.group(0)
        if w > h:
            result["aspect_ratio"] = "landscape"
        elif w < h:
            result["aspect_ratio"] = "portrait"
        else:
            result["aspect_ratio"] = "square"
        return result

    # 2. 纯数字组合 7501500 -> 尝试解析为 750x1500
    # 避免误匹配，只在前面没找到尺寸时才尝试
    pure_num_match = re.search(r"(\d{3,4})(\d{3,4})", t)
    if pure_num_match:
        w = int(pure_num_match.group(1))
        h = int(pure_num_match.group(2))
        # 简单校验：常见图片尺寸范围
        if 300 <= w <= 2048 and 300 <= h <= 2048 and w != h:
            result["target_size"] = [w, h]
            result["raw_size_text"] = pure_num_match.group(0)
            if w > h:
                result["aspect_ratio"] = "landscape"
            else:
                result["aspect_ratio"] = "portrait"
            return result

    # 3. 比例
    if "9:16" in t or "3:4" in t or "2:3" in t:
        result["aspect_ratio"] = "portrait"
        result["raw_size_text"] = re.search(r"\d+:\d+", t).group(0) if re.search(r"\d+:\d+", t) else "9:16"
        return result
    elif "16:9" in t or "21:9" in t or "3:2" in t or "4:3" in t:
        result["aspect_ratio"] = "landscape"
        result["raw_size_text"] = re.search(r"\d+:\d+", t).group(0) if re.search(r"\d+:\d+", t) else "16:9"
        return result
    elif "1:1" in t:
        result["aspect_ratio"] = "square"
        result["raw_size_text"] = "1:1"
        return result

    # 4. 竖版相关
    portrait_keywords = [
        "竖版", "竖屏", "小红书", "抖音", "视频号", "手机",
        "海报", "电商长图", "淘宝详情页", "详情页", "长图",
    ]
    if any(k in t for k in portrait_keywords):
        result["aspect_ratio"] = "portrait"
        matched = next((k for k in portrait_keywords if k in t), "竖版")
        result["raw_size_text"] = matched
        return result

    # 5. 横版相关
    landscape_keywords = [
        "横版", "横屏", "ppt", "banner", "头图", "封面",
        "电脑", "网页", "pc", "宽屏",
    ]
    if any(k in t for k in landscape_keywords):
        result["aspect_ratio"] = "landscape"
        matched = next((k for k in landscape_keywords if k in t), "横版")
        result["raw_size_text"] = matched
        return result

    # 6. 方图相关
    square_keywords = [
        "方图", "正方形", "方形", "头像", "商品主图",
        "1比1", "一比一",
    ]
    if any(k in t for k in square_keywords):
        result["aspect_ratio"] = "square"
        matched = next((k for k in square_keywords if k in t), "方图")
        result["raw_size_text"] = matched
        return result

    return result


def postprocess_image(input_path: str, target_size: list, output_path: str, bg_color=(255, 255, 255)) -> str:
    """
    将图片处理到目标尺寸，使用 cover + center crop 策略

    先生成最接近比例的图，然后 resize/crop 成目标尺寸
    """
    img = Image.open(input_path)
    target_w, target_h = target_size
    img_w, img_h = img.size

    # cover 策略：按比例缩放到能完全覆盖目标尺寸
    ratio = max(target_w / img_w, target_h / img_h)
    new_w = int(img_w * ratio)
    new_h = int(img_h * ratio)

    img_resized = img.resize((new_w, new_h), Image.LANCZOS)

    # center crop
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    right = left + target_w
    bottom = top + target_h

    img_cropped = img_resized.crop((left, top, right, bottom))

    # 处理模式转换
    if img_cropped.mode == "RGBA":
        background = Image.new("RGB", (target_w, target_h), bg_color)
        background.paste(img_cropped, mask=img_cropped.split()[3])
        img_cropped = background
    elif img_cropped.mode != "RGB":
        img_cropped = img_cropped.convert("RGB")

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img_cropped.save(output_path, quality=95)
    logger.info(f"图片后处理完成: {output_path} ({target_w}x{target_h})")
    return output_path


def acquire_generation_lock() -> bool:
    """
    获取全局生成锁
    返回 True 表示获取成功，False 表示当前有任务在运行
    """
    global _generation_in_progress
    with _generation_lock:
        if _generation_in_progress:
            return False
        _generation_in_progress = True
        return True


def release_generation_lock() -> None:
    """释放全局生成锁"""
    global _generation_in_progress
    with _generation_lock:
        _generation_in_progress = False
