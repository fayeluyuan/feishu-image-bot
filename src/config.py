"""
配置管理
从环境变量 / .env 文件读取所有配置
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


class Config:
    # 飞书配置
    FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
    FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
    FEISHU_ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "")

    # 图片生成默认比例
    DEFAULT_ASPECT_RATIO = os.getenv("DEFAULT_ASPECT_RATIO", "portrait")

    # ============================================
    # 烈鸟 API 配置
    # ============================================
    LIENIAO_API_KEY = os.getenv("LIENIAO_API_KEY", "")
    LIENIAO_GEMINI_API_KEY = os.getenv("LIENIAO_GEMINI_API_KEY", LIENIAO_API_KEY)
    LIENIAO_IMAGE2_API_KEY = os.getenv("LIENIAO_IMAGE2_API_KEY", LIENIAO_API_KEY)
    LIENIAO_DEFAULT_BACKEND = os.getenv("LIENIAO_DEFAULT_BACKEND", "gemini")
    LIENIAO_GEMINI_API_URL = os.getenv(
        "LIENIAO_GEMINI_API_URL",
        "https://lnapi.com/v1beta/models/{model}:generateContent",
    )
    LIENIAO_GEMINI_MODEL = os.getenv("LIENIAO_GEMINI_MODEL", "gemini-3-pro-image-preview")
    LIENIAO_IMAGE2_API_URL = os.getenv("LIENIAO_IMAGE2_API_URL", "https://lnapi.com/v1/images/generations")
    LIENIAO_IMAGE2_MODEL = os.getenv("LIENIAO_IMAGE2_MODEL", "gpt-image-2-all")
    LIENIAO_TIMEOUT = int(os.getenv("LIENIAO_TIMEOUT", "180"))
    LIENIAO_OUTPUT_DIR = os.getenv("LIENIAO_OUTPUT_DIR", "/tmp/feishu-image-bot/lieniao")
    FALLBACK_TO_HERMES = os.getenv("FALLBACK_TO_HERMES", "true").lower() == "true"

    # ============================================
    # OpenAI 官方配置
    # ============================================
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/images/generations")
    OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
    OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "120"))

    # ============================================
    # 阿里云百炼 (DashScope) 配置
    # ============================================
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_API_URL = os.getenv("DASHSCOPE_API_URL", "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis")
    DASHSCOPE_MODEL = os.getenv("DASHSCOPE_MODEL", "wanx-v1")
    DASHSCOPE_TIMEOUT = int(os.getenv("DASHSCOPE_TIMEOUT", "180"))

    # ============================================
    # 通用配置
    # ============================================
    IMAGE_OUTPUT_DIR = os.getenv("IMAGE_OUTPUT_DIR", "/tmp/feishu-image-bot/images")
    PROVIDERS_DIR = os.getenv("PROVIDERS_DIR", "")  # 自定义插件目录

    # 飞书参考图缓存配置
    REFERENCE_IMAGE_DIR = os.getenv("REFERENCE_IMAGE_DIR", "/tmp/feishu-image-bot/references")
    REFERENCE_IMAGE_TTL_SECONDS = int(os.getenv("REFERENCE_IMAGE_TTL_SECONDS", "1800"))

    # 其他
    PORT = int(os.getenv("PORT", "5000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # 兼容旧 Hermes 配置（不再使用，但保留读取避免报错）
    HERMES_CMD = os.getenv("HERMES_CMD", "hermes")
    HERMES_TIMEOUT = int(os.getenv("HERMES_TIMEOUT", "300"))
    DEFAULT_IMAGE_TOOL = os.getenv("DEFAULT_IMAGE_TOOL", "image_generate")
    ENABLE_CUSTOM_SIZE_POSTPROCESS = os.getenv("ENABLE_CUSTOM_SIZE_POSTPROCESS", "true").lower() == "true"
    HERMES_IMAGE_PROVIDER = os.getenv("HERMES_IMAGE_PROVIDER", "")
    HERMES_IMAGE_MODEL = os.getenv("HERMES_IMAGE_MODEL", "")

    @classmethod
    def validate(cls) -> list[str]:
        """检查必需配置是否完整，返回缺失项列表"""
        missing = []
        if not cls.FEISHU_APP_ID:
            missing.append("FEISHU_APP_ID")
        if not cls.FEISHU_APP_SECRET:
            missing.append("FEISHU_APP_SECRET")

        # 检查至少配置了一个生图服务
        has_image_provider = any([
            cls.LIENIAO_GEMINI_API_KEY,
            cls.LIENIAO_IMAGE2_API_KEY,
            cls.OPENAI_API_KEY,
            cls.DASHSCOPE_API_KEY,
        ])
        if not has_image_provider:
            missing.append("至少一个图片生成 API Key（LIENIAO_GEMINI_API_KEY / OPENAI_API_KEY / DASHSCOPE_API_KEY）")

        return missing
