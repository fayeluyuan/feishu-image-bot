"""
图片生成适配器（插件化架构 v3.0）
自动检测并调用已配置的图片生成服务
"""
import logging

from providers import GenerationResult
from providers.registry import get_available_providers, get_provider

logger = logging.getLogger(__name__)


class ImageGenerator:
    """图片生成器 - 自动调度多个提供商"""

    def __init__(self):
        self._providers = get_available_providers()
        if not self._providers:
            logger.error("[ImageGen] 错误：未配置任何图片生成服务！请检查 .env 文件")

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "portrait",
        target_size: list | None = None,
        reference_images: list[str] | None = None,
        preferred_provider: str | None = None,
    ) -> dict:
        """
        生成图片，自动选择已配置的提供商

        Args:
            prompt: 用户提示词
            aspect_ratio: 比例关键词
            target_size: 自定义尺寸 [宽, 高]
            reference_images: 参考图路径列表
            preferred_provider: 优先使用的提供商名称（如 "openai", "lieniao"）

        Returns:
            dict: {"success": bool, "image_path": str|None, "tool_used": str, "error": str|None}
        """
        # 获取提供商实例
        provider = get_provider(preferred_provider)
        if not provider:
            return {
                "success": False,
                "image_path": None,
                "tool_used": "",
                "error": "未配置任何图片生成服务。请在 .env 中配置至少一个 API Key：\n"
                        "- LIENIAO_GEMINI_API_KEY 或 LIENIAO_IMAGE2_API_KEY（烈鸟）\n"
                        "- OPENAI_API_KEY（OpenAI 官方）\n"
                        "- DASHSCOPE_API_KEY（阿里云百炼）",
            }

        logger.info(f"[ImageGen] 使用提供商 '{provider.name}' 生成图片: {prompt[:50]}...")

        # 调用生成
        result: GenerationResult = provider.generate(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            target_size=target_size,
            reference_images=reference_images,
        )

        # 如果失败且有其他提供商，尝试 fallback
        if not result.success and len(self._providers) > 1:
            logger.warning(f"[ImageGen] {provider.name} 失败，尝试其他提供商...")
            for cls in self._providers:
                if cls.name == provider.name:
                    continue
                fallback = cls()
                logger.info(f"[ImageGen] Fallback 到 {fallback.name}")
                result = fallback.generate(
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    target_size=target_size,
                    reference_images=reference_images,
                )
                if result.success:
                    break

        return {
            "success": result.success,
            "image_path": result.image_path,
            "tool_used": result.tool_used,
            "error": result.error,
        }


def get_image_generator() -> ImageGenerator:
    """工厂函数"""
    return ImageGenerator()
