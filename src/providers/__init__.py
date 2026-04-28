"""
图片生成提供商基类
所有生图服务必须继承此类，实现 generate() 方法
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class GenerationResult:
    """统一的生成结果格式"""
    success: bool
    image_path: Optional[str] = None
    tool_used: str = ""
    error: Optional[str] = None


class BaseProvider(ABC):
    """生图服务提供商基类"""

    # 提供商标识名，如 "openai", "lieniao", "dashscope"
    name: str = ""

    # 环境变量中检测的 API Key 名称列表
    # 例如 ["OPENAI_API_KEY"]
    required_keys: list[str] = []

    @classmethod
    @abstractmethod
    def is_configured(cls) -> bool:
        """检查当前环境是否配置了这个提供商"""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "portrait",
        target_size: Optional[list] = None,
        reference_images: Optional[list[str]] = None,
    ) -> GenerationResult:
        """
        生成图片

        Args:
            prompt: 用户提示词
            aspect_ratio: 比例关键词 (portrait/landscape/square)
            target_size: 自定义尺寸 [宽, 高]
            reference_images: 参考图路径列表（可选）

        Returns:
            GenerationResult: 统一结果格式
        """
        pass

    def _size_from_ratio(self, aspect_ratio: str) -> str:
        """通用比例转尺寸"""
        ratio = (aspect_ratio or "portrait").lower()
        mapping = {
            "portrait": "1024x1792",
            "landscape": "1792x1024",
            "square": "1024x1024",
            "9:16": "1024x1792",
            "16:9": "1792x1024",
            "1:1": "1024x1024",
            "3:4": "1024x1536",
            "4:3": "1536x1024",
        }
        return mapping.get(ratio, "1024x1024")
