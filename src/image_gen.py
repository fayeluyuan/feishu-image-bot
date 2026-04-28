"""
图片生成适配器
v3.0: 默认直连烈鸟 API（Gemini-3-Pro）；用户指定 image2/gpt-image-2 时切换烈鸟 image2 分组。
      Hermes CLI 保留为兜底方案。
"""
import logging

from config import Config
from hermes_client import HermesMediaGenerator
from lieniao_client import LieniaoImageGenerator

logger = logging.getLogger(__name__)


class ImageGenerator:
    """图片生成器"""

    def __init__(self):
        self._lieniao = LieniaoImageGenerator()
        self._hermes = HermesMediaGenerator()

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "portrait",
        target_size: list | None = None,
        reference_images: list[str] | None = None,
    ) -> dict:
        """
        生成图片。优先烈鸟 API，失败时可按配置 fallback 到 Hermes。

        返回 dict:
        {
            "success": bool,
            "image_path": str | None,
            "tool_used": str,
            "error": str | None,
        }
        """
        if self._lieniao.is_configured():
            logger.info(f"[ImageGen] 通过烈鸟 API 生成图片: {prompt[:50]}... 比例={aspect_ratio}")
            result = self._lieniao.generate(prompt, aspect_ratio, target_size, reference_images=reference_images)
            if result.success:
                return {
                    "success": True,
                    "image_path": result.image_path,
                    "tool_used": result.tool_used,
                    "error": None,
                }
            logger.warning(f"[ImageGen] 烈鸟 API 失败: {result.error}")
            if not Config.FALLBACK_TO_HERMES:
                return {
                    "success": False,
                    "image_path": None,
                    "tool_used": result.tool_used,
                    "error": result.error,
                }

        logger.info(f"[ImageGen] 通过 Hermes 兜底生成图片: {prompt[:50]}... 比例={aspect_ratio}")
        if reference_images:
            logger.warning("[ImageGen] Hermes 兜底暂不支持参考图，将按纯文本请求生成")
        return self._hermes.generate_image(prompt, aspect_ratio, target_size)


def get_image_generator() -> ImageGenerator:
    """工厂函数"""
    return ImageGenerator()
