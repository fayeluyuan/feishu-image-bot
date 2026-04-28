"""
视频生成模块
v1.0: 占位，只返回提示信息
"""
import logging

logger = logging.getLogger(__name__)


class VideoGenerator:
    """视频生成器（v1.0 占位）"""

    def generate(self, prompt: str, duration: int = 5, ratio: str = "16:9") -> bytes:
        """
        v1.0 不实现真实视频生成。
        gpt-image-2-medium 是图片模型，不能直接生成视频。
        """
        text = (
            "当前 gpt-image-2-medium 是图片模型，不能直接生成视频。"
            "视频需要接入 Veo / 可灵 / Runway / Sora / Seedance 等视频模型。"
        )
        logger.warning(f"[VideoGen] 收到视频请求但 v1.0 不支持: {prompt[:50]}...")
        return text.encode("utf-8")


def get_video_generator() -> VideoGenerator:
    """工厂函数"""
    return VideoGenerator()
