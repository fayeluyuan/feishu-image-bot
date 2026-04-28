"""
阿里云百炼 (DashScope) 图片生成提供商
支持通义万相 (Wanx) 等模型
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


class DashScopeProvider(BaseProvider):
    """阿里云百炼 / DashScope 提供商"""

    name = "dashscope"
    required_keys = ["DASHSCOPE_API_KEY"]

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.api_url = os.getenv("DASHSCOPE_API_URL", "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis")
        self.model = os.getenv("DASHSCOPE_MODEL", "wanx-v1")
        self.timeout = int(os.getenv("DASHSCOPE_TIMEOUT", "180"))
        self.output_dir = Path(os.getenv("IMAGE_OUTPUT_DIR", "/tmp/feishu-image-bot/images"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def is_configured(cls) -> bool:
        return bool(os.getenv("DASHSCOPE_API_KEY", ""))

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "portrait",
        target_size: Optional[list] = None,
        reference_images: Optional[list[str]] = None,
    ) -> GenerationResult:
        if reference_images:
            logger.warning("[DashScope] 当前不支持参考图功能，将忽略参考图")

        # 百炼尺寸映射
        ratio = (aspect_ratio or "portrait").lower()
        size_map = {
            "portrait": "1024x1536",
            "landscape": "1536x1024",
            "square": "1024x1024",
            "9:16": "1024x1536",
            "16:9": "1536x1024",
            "1:1": "1024x1024",
        }
        size = size_map.get(ratio, "1024x1024")
        if target_size:
            size = f"{target_size[0]}x{target_size[1]}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "input": {
                "prompt": prompt,
            },
            "parameters": {
                "size": size,
                "n": 1,
            }
        }

        try:
            logger.info(f"[DashScope] 请求 model={self.model} size={size}")
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            # 百炼是异步接口，需要轮询任务结果
            task_id = data.get("output", {}).get("task_id")
            if not task_id:
                return GenerationResult(False, error="百炼未返回任务ID")

            # 轮询结果
            result = self._poll_task(task_id)
            return result

        except requests.exceptions.RequestException as e:
            return GenerationResult(False, error=f"百炼请求失败: {str(e)}")
        except Exception as e:
            return GenerationResult(False, error=f"百炼处理异常: {str(e)}")

    def _poll_task(self, task_id: str) -> GenerationResult:
        """轮询百炼异步任务结果"""
        task_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        max_retries = 30
        for i in range(max_retries):
            try:
                resp = requests.get(task_url, headers=headers, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                status = data.get("output", {}).get("task_status", "")
                if status == "SUCCEEDED":
                    # 提取图片
                    results = data.get("output", {}).get("results", [])
                    if not results:
                        return GenerationResult(False, error="百炼任务成功但无图片")

                    img_url = results[0].get("url")
                    if not img_url:
                        return GenerationResult(False, error="百炼返回中无图片URL")

                    # 下载图片
                    img_resp = requests.get(img_url, timeout=60)
                    img_resp.raise_for_status()
                    image_data = img_resp.content

                    ext = ".png"
                    if image_data.startswith(b"\xff\xd8\xff"):
                        ext = ".jpg"
                    filename = f"dashscope_{int(time.time()*1000)}{ext}"
                    filepath = self.output_dir / filename
                    filepath.write_bytes(image_data)

                    return GenerationResult(
                        success=True,
                        image_path=str(filepath),
                        tool_used=f"dashscope/{self.model}",
                    )

                elif status in ("FAILED", "ERROR"):
                    error_msg = data.get("output", {}).get("message", "未知错误")
                    return GenerationResult(False, error=f"百炼任务失败: {error_msg}")

                # 继续轮询
                time.sleep(2)

            except Exception as e:
                return GenerationResult(False, error=f"百炼轮询异常: {e}")

        return GenerationResult(False, error="百炼任务轮询超时")
