"""
OpenAI 官方图片生成提供商
支持 DALL-E 2 / DALL-E 3 / GPT-Image-2
"""
import base64
import logging
import os
import time
from pathlib import Path
from typing import Optional

import requests

from providers import BaseProvider, GenerationResult

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI 官方 DALL-E / GPT-Image 提供商"""

    name = "openai"
    required_keys = ["OPENAI_API_KEY"]

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.api_url = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/images/generations")
        self.model = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
        self.timeout = int(os.getenv("OPENAI_TIMEOUT", "120"))
        self.output_dir = Path(os.getenv("IMAGE_OUTPUT_DIR", "/tmp/feishu-image-bot/images"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def is_configured(cls) -> bool:
        return bool(os.getenv("OPENAI_API_KEY", ""))

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "portrait",
        target_size: Optional[list] = None,
        reference_images: Optional[list[str]] = None,
    ) -> GenerationResult:
        if reference_images:
            logger.warning("[OpenAI] 当前不支持参考图功能，将忽略参考图")

        size = self._size_from_ratio(aspect_ratio)
        if target_size:
            size = f"{target_size[0]}x{target_size[1]}"

        # DALL-E 3 只支持固定尺寸，需要映射
        if "dall-e-3" in self.model:
            size_map = {
                "1024x1792": "1024x1792",
                "1792x1024": "1792x1024",
                "1024x1024": "1024x1024",
            }
            size = size_map.get(size, "1024x1024")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "response_format": "b64_json",
        }

        try:
            logger.info(f"[OpenAI] 请求 model={self.model} size={size}")
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            # 解析图片
            images = data.get("data", [])
            if not images:
                return GenerationResult(False, error="OpenAI 返回空图片列表")

            b64_data = images[0].get("b64_json")
            if not b64_data:
                # 可能是 URL 格式
                url = images[0].get("url")
                if url:
                    img_resp = requests.get(url, timeout=60)
                    img_resp.raise_for_status()
                    image_data = img_resp.content
                else:
                    return GenerationResult(False, error="OpenAI 返回中无图片数据")
            else:
                image_data = base64.b64decode(b64_data)

            # 保存
            ext = ".png"
            if image_data.startswith(b"\xff\xd8\xff"):
                ext = ".jpg"
            filename = f"openai_{int(time.time()*1000)}{ext}"
            filepath = self.output_dir / filename
            filepath.write_bytes(image_data)

            return GenerationResult(
                success=True,
                image_path=str(filepath),
                tool_used=f"openai/{self.model}",
            )

        except requests.exceptions.RequestException as e:
            return GenerationResult(False, error=f"OpenAI 请求失败: {str(e)}")
        except Exception as e:
            return GenerationResult(False, error=f"OpenAI 处理异常: {str(e)}")
