"""
媒体生成客户端（无 Hermes 依赖版）
- 直接调用烈鸟 API（Gemini / OpenAI 兼容端点）
- 支持多后端切换：gemini-3-pro-image-preview / gpt-image-2-all
"""
import json
import logging
import os
import time
from typing import Optional

import requests

from config import Config

logger = logging.getLogger(__name__)


class MediaGenerator:
    """直接调用烈鸟 API 生成图片"""

    def __init__(self):
        self.default_ratio = Config.DEFAULT_ASPECT_RATIO
        self.timeout = Config.LIENIAO_TIMEOUT

        # Gemini 后端配置
        self.gemini_key = Config.LIENIAO_GEMINI_API_KEY
        self.gemini_url = Config.LIENIAO_GEMINI_API_URL
        self.gemini_model = Config.LIENIAO_GEMINI_MODEL

        # Image2 (OpenAI 兼容) 后端配置
        self.image2_key = Config.LIENIAO_IMAGE2_API_KEY
        self.image2_url = Config.LIENIAO_IMAGE2_API_URL
        self.image2_model = Config.LIENIAO_IMAGE2_MODEL

        # 默认后端
        self.default_backend = Config.LIENIAO_DEFAULT_BACKEND
        self.fallback_to_image2 = Config.FALLBACK_TO_HERMES  # 复用配置项：fallback 到 image2

        # 输出目录
        self.output_dir = Config.LIENIAO_OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def _select_backend(self, prompt: str) -> str:
        """根据用户提示词选择后端"""
        prompt_lower = prompt.lower()
        if any(k in prompt_lower for k in ["image2", "gpt-image-2", "openai", "dall-e"]):
            return "image2"
        if any(k in prompt_lower for k in ["gemini", "烈鸟", "gemini-3-pro"]):
            return "gemini"
        return self.default_backend

    def _call_gemini(self, prompt: str, aspect_ratio: str = "portrait") -> dict:
        """调用烈鸟 Gemini 后端"""
        if not self.gemini_key:
            return {"success": False, "error": "LIENIAO_GEMINI_API_KEY 未配置"}

        url = self.gemini_url.format(model=self.gemini_model)
        headers = {
            "Authorization": f"Bearer {self.gemini_key}",
            "Content-Type": "application/json",
        }

        # 尺寸映射
        size_map = {
            "portrait": {"width": 1024, "height": 1536},
            "landscape": {"width": 1536, "height": 1024},
            "square": {"width": 1024, "height": 1024},
        }
        size = size_map.get(aspect_ratio, size_map["portrait"])

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "temperature": 0.7,
            }
        }

        try:
            logger.info(f"[烈鸟 Gemini] 请求: {prompt[:60]}...")
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            # 解析图片数据
            candidates = data.get("candidates", [])
            if not candidates:
                return {"success": False, "error": "Gemini 返回空 candidates"}

            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                if "inlineData" in part:
                    import base64
                    img_data = base64.b64decode(part["inlineData"]["data"])
                    # 保存文件
                    ext = part["inlineData"].get("mimeType", "image/png").split("/")[-1]
                    if ext == "jpeg":
                        ext = "jpg"
                    filename = f"gemini_{int(time.time()*1000)}.{ext}"
                    filepath = os.path.join(self.output_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(img_data)
                    return {
                        "success": True,
                        "image_path": filepath,
                        "tool_used": f"lieniao/gemini/{self.gemini_model}",
                        "error": None,
                    }

            return {"success": False, "error": "Gemini 返回中未找到图片数据"}

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"烈鸟 Gemini 请求失败: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Gemini 处理异常: {str(e)}"}

    def _call_image2(self, prompt: str, aspect_ratio: str = "portrait", target_size: Optional[list] = None) -> dict:
        """调用烈鸟 Image2 (OpenAI 兼容) 后端"""
        if not self.image2_key:
            return {"success": False, "error": "LIENIAO_IMAGE2_API_KEY 未配置"}

        headers = {
            "Authorization": f"Bearer {self.image2_key}",
            "Content-Type": "application/json",
        }

        # 尺寸映射
        size_map = {
            "portrait": "1024x1536",
            "landscape": "1536x1024",
            "square": "1024x1024",
        }
        size = size_map.get(aspect_ratio, "1024x1536")
        if target_size:
            size = f"{target_size[0]}x{target_size[1]}"

        payload = {
            "model": self.image2_model,
            "prompt": prompt,
            "size": size,
            "n": 1,
        }

        try:
            logger.info(f"[烈鸟 Image2] 请求: {prompt[:60]}... 尺寸: {size}")
            resp = requests.post(self.image2_url, headers=headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            # 解析图片 URL
            images = data.get("data", [])
            if not images or not images[0].get("url"):
                return {"success": False, "error": f"Image2 返回异常: {json.dumps(data)[:500]}"}

            img_url = images[0]["url"]
            # 下载图片
            img_resp = requests.get(img_url, timeout=60)
            img_resp.raise_for_status()

            ext = "png"
            content_type = img_resp.headers.get("Content-Type", "")
            if "jpeg" in content_type or "jpg" in content_type:
                ext = "jpg"

            filename = f"image2_{int(time.time()*1000)}.{ext}"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(img_resp.content)

            return {
                "success": True,
                "image_path": filepath,
                "tool_used": f"lieniao/image2/{self.image2_model}",
                "error": None,
            }

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"烈鸟 Image2 请求失败: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Image2 处理异常: {str(e)}"}

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "portrait",
        target_size: Optional[list] = None,
    ) -> dict:
        """
        生成图片

        返回:
        {
            "success": bool,
            "image_path": str | None,
            "tool_used": str,
            "error": str | None,
        }
        """
        backend = self._select_backend(prompt)
        logger.info(f"[MediaGenerator] 选择后端: {backend}, 比例: {aspect_ratio}")

        if backend == "gemini":
            result = self._call_gemini(prompt, aspect_ratio)
            # Gemini 失败且允许 fallback，尝试 image2
            if not result["success"] and self.fallback_to_image2 and self.image2_key:
                logger.info(f"[MediaGenerator] Gemini 失败，fallback 到 image2: {result['error']}")
                result = self._call_image2(prompt, aspect_ratio, target_size)
            return result

        else:  # image2
            return self._call_image2(prompt, aspect_ratio, target_size)


def get_hermes_generator() -> MediaGenerator:
    """工厂函数（保持兼容旧接口）"""
    return MediaGenerator()
