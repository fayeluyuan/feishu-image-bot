"""
烈鸟 API 图片生成提供商
支持 Gemini 原生端点 + OpenAI 兼容端点
"""
import base64
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional

import requests

# 确保 .env 被加载（直接运行此文件时）
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)

from providers import BaseProvider, GenerationResult

logger = logging.getLogger(__name__)


class LieniaoProvider(BaseProvider):
    """烈鸟 API 提供商（Gemini + Image2 双端点）"""

    name = "lieniao"
    required_keys = ["LIENIAO_API_KEY", "LIENIAO_GEMINI_API_KEY", "LIENIAO_IMAGE2_API_KEY"]

    def __init__(self):
        self.api_key = os.getenv("LIENIAO_API_KEY", "")
        self.gemini_api_key = os.getenv("LIENIAO_GEMINI_API_KEY", self.api_key)
        self.image2_api_key = os.getenv("LIENIAO_IMAGE2_API_KEY", self.api_key)
        self.default_backend = os.getenv("LIENIAO_DEFAULT_BACKEND", "gemini")
        self.gemini_api_url = os.getenv(
            "LIENIAO_GEMINI_API_URL",
            "https://lnapi.com/v1beta/models/{model}:generateContent",
        )
        self.gemini_model = os.getenv("LIENIAO_GEMINI_MODEL", "gemini-3-pro-image-preview")
        self.image2_api_url = os.getenv("LIENIAO_IMAGE2_API_URL", "https://lnapi.com/v1/images/generations")
        self.image2_model = os.getenv("LIENIAO_IMAGE2_MODEL", "gpt-image-2-all")
        self.timeout = int(os.getenv("LIENIAO_TIMEOUT", "180"))
        self.output_dir = Path(os.getenv("LIENIAO_OUTPUT_DIR", "/tmp/feishu-image-bot/lieniao"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def is_configured(cls) -> bool:
        return bool(
            os.getenv("LIENIAO_API_KEY", "")
            or os.getenv("LIENIAO_GEMINI_API_KEY", "")
            or os.getenv("LIENIAO_IMAGE2_API_KEY", "")
        )

    def _select_backend(self, prompt: str) -> str:
        """根据用户提示词选择后端"""
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
    ) -> GenerationResult:
        backend = "gemini" if reference_images else self._select_backend(prompt)

        if backend == "image2":
            return self._generate_image2(prompt, aspect_ratio)
        return self._generate_gemini(prompt, aspect_ratio, reference_images)

    def _headers(self, backend: str = "gemini") -> dict:
        api_key = self.gemini_api_key if backend == "gemini" else self.image2_api_key
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def _save_image(self, image_data: bytes, prefix: str) -> str:
        ext = ".png"
        if image_data.startswith(b"\xff\xd8\xff"):
            ext = ".jpg"
        elif image_data.startswith(b"RIFF"):
            ext = ".webp"
        path = self.output_dir / f"{prefix}_{int(time.time()*1000)}{ext}"
        path.write_bytes(image_data)
        return str(path)

    def _extract_image(self, data: dict) -> tuple[Optional[bytes], Optional[str]]:
        """从响应中提取图片数据或URL"""
        # Gemini inlineData
        if isinstance(data, dict):
            for key in ("inlineData", "inline_data"):
                if key in data and isinstance(data[key], dict):
                    b64 = data[key].get("data")
                    if b64:
                        return base64.b64decode(b64), None
            # 常见 b64 字段
            for key in ("b64_json", "image_b64", "base64", "imageData"):
                val = data.get(key)
                if isinstance(val, str) and len(val) > 100:
                    try:
                        return base64.b64decode(val.split(",", 1)[-1]), None
                    except Exception:
                        pass
            # URL 字段
            for key in ("url", "image_url", "imageUrl", "download_url"):
                val = data.get(key)
                if isinstance(val, str) and val.startswith("http"):
                    return None, val
            # 递归查找
            for val in data.values():
                if isinstance(val, (dict, list)):
                    img, url = self._extract_image(val)
                    if img or url:
                        return img, url
        elif isinstance(data, list):
            for item in data:
                img, url = self._extract_image(item)
                if img or url:
                    return img, url
        return None, None

    def _generate_gemini(self, prompt: str, aspect_ratio: str, reference_images: Optional[list[str]] = None) -> GenerationResult:
        ratio = self._normalize_ratio(aspect_ratio)
        model = self.gemini_model
        url = self.gemini_api_url.format(model=model)

        parts = []
        for img_path in reference_images or []:
            parts.append(self._reference_part(img_path))
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
            logger.info(f"[Lieniao] Gemini 请求 model={model} ratio={ratio}")
            resp = requests.post(url, json=payload, headers=self._headers("gemini"), timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            image_data, image_url = self._extract_image(data)
            if image_url and not image_data:
                image_data = requests.get(image_url, timeout=60).content
            if not image_data:
                return GenerationResult(False, error="烈鸟 Gemini 返回中未找到图片")

            path = self._save_image(image_data, "lieniao_gemini")
            return GenerationResult(True, image_path=path, tool_used=f"lieniao/{model}")

        except Exception as e:
            return GenerationResult(False, error=f"烈鸟 Gemini 调用异常: {e}")

    def _generate_image2(self, prompt: str, aspect_ratio: str) -> GenerationResult:
        model = self.image2_model
        size = self._size_from_ratio(aspect_ratio)

        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "response_format": "b64_json",
        }

        try:
            logger.info(f"[Lieniao] Image2 请求 model={model} size={size}")
            resp = requests.post(self.image2_api_url, json=payload, headers=self._headers("image2"), timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            image_data, image_url = self._extract_image(data)
            if image_url and not image_data:
                image_data = requests.get(image_url, timeout=60).content
            if not image_data:
                return GenerationResult(False, error="烈鸟 Image2 返回中未找到图片")

            path = self._save_image(image_data, "lieniao_image2")
            return GenerationResult(True, image_path=path, tool_used=f"lieniao/{model}")

        except Exception as e:
            return GenerationResult(False, error=f"烈鸟 Image2 调用异常: {e}")

    def _normalize_ratio(self, aspect_ratio: str) -> str:
        mapping = {
            "portrait": "9:16",
            "landscape": "16:9",
            "square": "1:1",
        }
        return mapping.get((aspect_ratio or "portrait").lower(), "9:16")

    def _reference_part(self, image_path: str) -> dict:
        """把本地参考图转成 Gemini inline_data part"""
        path = Path(image_path)
        image_data = path.read_bytes()

        mime = "image/png"
        if image_data.startswith(b"\xff\xd8\xff"):
            mime = "image/jpeg"
        elif image_data.startswith(b"\x89PNG"):
            mime = "image/png"
        elif image_data.startswith(b"RIFF"):
            mime = "image/webp"

        return {
            "inlineData": {
                "mimeType": mime,
                "data": base64.b64encode(image_data).decode("utf-8"),
            }
        }
