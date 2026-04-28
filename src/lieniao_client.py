"""
烈鸟 API 图片生成客户端

支持两类分组/端点：
1. Gemini 原生兼容端点：/v1beta/models/{model}:generateContent
   默认模型：gemini-3-pro-image-preview
2. OpenAI Images 兼容端点：/v1/images/generations
   默认模型：gpt-image-2-medium（烈鸟 image2 分组）

机器人默认走 Gemini；用户消息包含 image2/gpt-image-2/OpenAI 时切换到 image2。
"""
import base64
import logging
import mimetypes
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

from config import Config

logger = logging.getLogger(__name__)


@dataclass
class LieniaoResult:
    success: bool
    image_path: Optional[str] = None
    tool_used: str = "lieniao"
    error: Optional[str] = None


def normalize_ratio(aspect_ratio: str) -> str:
    """把机器人内部比例名转成 Gemini/OpenAI API 常见比例。"""
    mapping = {
        "portrait": "9:16",
        "landscape": "16:9",
        "square": "1:1",
        "custom": "1:1",
        "9:16": "9:16",
        "16:9": "16:9",
        "1:1": "1:1",
        "3:4": "3:4",
        "4:3": "4:3",
    }
    return mapping.get((aspect_ratio or "portrait").lower(), "9:16")


def size_from_ratio(aspect_ratio: str, model: str = "") -> str:
    """OpenAI Images 端点尺寸；兼容 image2/gpt-image-2 和 DALL-E 风格尺寸。"""
    ratio = normalize_ratio(aspect_ratio)
    if ratio in ("16:9", "4:3"):
        return "1792x1024"
    if ratio in ("9:16", "3:4"):
        return "1024x1792"
    return "1024x1024"


class LieniaoImageGenerator:
    def __init__(self):
        self.api_key = Config.LIENIAO_API_KEY
        self.gemini_api_key = Config.LIENIAO_GEMINI_API_KEY
        self.image2_api_key = Config.LIENIAO_IMAGE2_API_KEY
        self.default_backend = Config.LIENIAO_DEFAULT_BACKEND
        self.gemini_api_url = Config.LIENIAO_GEMINI_API_URL
        self.gemini_model = Config.LIENIAO_GEMINI_MODEL
        self.image2_api_url = Config.LIENIAO_IMAGE2_API_URL
        self.image2_model = Config.LIENIAO_IMAGE2_MODEL
        self.timeout = Config.LIENIAO_TIMEOUT
        self.output_dir = Path(Config.LIENIAO_OUTPUT_DIR).expanduser()

    def is_configured(self) -> bool:
        return bool(self.gemini_api_key or self.image2_api_key or self.api_key)

    def select_backend(self, prompt: str) -> str:
        t = (prompt or "").lower()
        if any(k in t for k in ["image2", "image 2", "gpt-image-2", "gpt image 2", "openai"]):
            return "image2"
        if any(k in t for k in ["烈鸟", "lieniao", "lnapi", "gemini", "nano banana", "nano-banana"]):
            return "gemini"
        return self.default_backend or "gemini"

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "portrait",
        target_size: Optional[list] = None,
        reference_images: Optional[list[str]] = None,
    ) -> LieniaoResult:
        if not self.is_configured():
            return LieniaoResult(False, error="未配置 LIENIAO_API_KEY")
        # 有参考图时优先强制走 Gemini 原生多模态端点；当前 image2 generations 端点不接收参考图。
        backend = "gemini" if reference_images else self.select_backend(prompt)
        if backend == "image2":
            return self._generate_image2(prompt, aspect_ratio)
        return self._generate_gemini(prompt, aspect_ratio, reference_images=reference_images)

    def _headers(self, backend: str = "gemini") -> dict:
        api_key = self.gemini_api_key if backend == "gemini" else self.image2_api_key
        api_key = api_key or self.api_key
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def _save_image(self, image_data: bytes, backend: str) -> str:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # 简单判断扩展名
        ext = ".png"
        if image_data.startswith(b"\xff\xd8\xff"):
            ext = ".jpg"
        elif image_data.startswith(b"RIFF"):
            ext = ".webp"
        path = self.output_dir / f"{backend}_{int(time.time())}{ext}"
        path.write_bytes(image_data)
        return str(path)

    def _reference_part(self, image_path: str) -> dict:
        """把本地参考图转成 Gemini inline_data part。"""
        path = Path(image_path)
        image_data = path.read_bytes()
        mime_type = mimetypes.guess_type(str(path))[0]
        if not mime_type or not mime_type.startswith("image/"):
            if image_data.startswith(b"\xff\xd8\xff"):
                mime_type = "image/jpeg"
            elif image_data.startswith(b"\x89PNG\r\n\x1a\n"):
                mime_type = "image/png"
            elif image_data.startswith(b"RIFF"):
                mime_type = "image/webp"
            else:
                mime_type = "image/png"
        return {
            "inlineData": {
                "mimeType": mime_type,
                "data": base64.b64encode(image_data).decode("utf-8"),
            }
        }

    def _extract_image_from_json(self, data) -> tuple[Optional[bytes], Optional[str]]:
        """递归提取 b64 图片或 URL，兼容 OpenAI/Gemini/聚合 API 多种返回。"""
        if isinstance(data, dict):
            # Gemini inlineData / inline_data
            for inline_key in ("inlineData", "inline_data"):
                if inline_key in data and isinstance(data[inline_key], dict):
                    b64 = data[inline_key].get("data")
                    if b64:
                        return base64.b64decode(b64), None
            # 常见 b64 字段
            for key in ("b64_json", "image_b64", "image_base64", "base64", "imageData"):
                val = data.get(key)
                if isinstance(val, str) and len(val) > 100:
                    try:
                        return base64.b64decode(val.split(",", 1)[-1]), None
                    except Exception:
                        pass
            # URL 字段
            for key in ("url", "image_url", "imageUrl", "fileUri", "download_url"):
                val = data.get(key)
                if isinstance(val, str) and val.startswith("http"):
                    return None, val
            for val in data.values():
                img, url = self._extract_image_from_json(val)
                if img or url:
                    return img, url
        elif isinstance(data, list):
            for item in data:
                img, url = self._extract_image_from_json(item)
                if img or url:
                    return img, url
        return None, None

    def _download(self, url: str) -> Optional[bytes]:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        return resp.content

    def _generate_gemini(self, prompt: str, aspect_ratio: str, reference_images: Optional[list[str]] = None) -> LieniaoResult:
        ratio = normalize_ratio(aspect_ratio)
        model = self.gemini_model or "gemini-3-pro-image-preview"
        base_url = self.gemini_api_url
        if "{model}" in base_url:
            url = base_url.format(model=model)
        elif "generateContent" in base_url:
            url = base_url
        else:
            url = base_url.rstrip("/") + f"/v1beta/models/{model}:generateContent"

        parts = []
        for image_path in reference_images or []:
            parts.append(self._reference_part(image_path))
        parts.append({"text": f"{prompt}\n\n请生成一张图片，画幅比例：{ratio}。"})

        payload = {
            "contents": [{
                "role": "user",
                "parts": parts,
            }],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "aspectRatio": ratio,
            },
        }
        try:
            logger.info("[Lieniao] Gemini 请求 model=%s ratio=%s", model, ratio)
            resp = requests.post(url, json=payload, headers=self._headers("gemini"), timeout=self.timeout)
            if resp.status_code != 200:
                return LieniaoResult(False, tool_used=f"lieniao/{model}", error=self._format_error(resp, model))
            data = resp.json()
            image_data, image_url = self._extract_image_from_json(data)
            if image_url and not image_data:
                image_data = self._download(image_url)
            if not image_data:
                return LieniaoResult(False, tool_used=f"lieniao/{model}", error=f"烈鸟 Gemini 返回中未找到图片: {str(data)[:500]}")
            path = self._save_image(image_data, "lieniao_gemini")
            return LieniaoResult(True, image_path=path, tool_used=f"lieniao/{model}")
        except Exception as e:
            return LieniaoResult(False, tool_used=f"lieniao/{model}", error=f"烈鸟 Gemini 调用异常: {e}")

    def _generate_image2(self, prompt: str, aspect_ratio: str) -> LieniaoResult:
        model = self.image2_model or "gpt-image-2-all"
        url = self.image2_api_url.rstrip("/")
        size = size_from_ratio(aspect_ratio, model)
        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "response_format": "b64_json",
        }
        try:
            logger.info("[Lieniao] image2 请求 model=%s size=%s url=%s", model, size, re.sub(r'/v1/.*$', '/v1/***', url))
            resp = requests.post(url, json=payload, headers=self._headers("image2"), timeout=self.timeout)
            if resp.status_code != 200:
                return LieniaoResult(False, tool_used=f"lieniao/{model}", error=self._format_error(resp, model))
            data = resp.json()
            image_data, image_url = self._extract_image_from_json(data)
            if image_url and not image_data:
                image_data = self._download(image_url)
            if not image_data:
                return LieniaoResult(False, tool_used=f"lieniao/{model}", error=f"烈鸟 image2 返回中未找到图片: {str(data)[:500]}")
            path = self._save_image(image_data, "lieniao_image2")
            return LieniaoResult(True, image_path=path, tool_used=f"lieniao/{model}")
        except Exception as e:
            return LieniaoResult(False, tool_used=f"lieniao/{model}", error=f"烈鸟 image2 调用异常: {e}")

    def _format_error(self, resp: requests.Response, model: str) -> str:
        body = resp.text[:800]
        msg = f"HTTP {resp.status_code}"
        try:
            data = resp.json()
            err = data.get("error") or data.get("message") or data
            if isinstance(err, dict):
                msg += f": {err.get('message') or err}"
            else:
                msg += f": {err}"
        except Exception:
            msg += f": {body}"
        if resp.status_code == 401:
            msg += "\n授权失败：请检查 LIENIAO_API_KEY 是否正确/过期。"
        elif resp.status_code == 404:
            msg += "\n端点不存在：请检查当前分组的网址是否正确。"
        elif resp.status_code == 503:
            msg += f"\n服务不可用：当前烈鸟 API 分组可能不支持模型 {model}，需要切换分组网址或模型。"
        return msg
