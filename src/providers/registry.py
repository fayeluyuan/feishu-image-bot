"""
提供商注册器
自动发现并加载所有已配置的图片生成服务
"""
import importlib
import inspect
import logging
import os
import sys
from pathlib import Path

# 确保 .env 被加载（providers 包被直接导入时）
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)

from providers import BaseProvider

logger = logging.getLogger(__name__)

# 内置提供商列表（按优先级排序）
BUILTIN_PROVIDERS = [
    "providers.lieniao",      # 烈鸟（推荐，性价比高）
    "providers.openai",         # OpenAI 官方
    "providers.dashscope",      # 阿里云百炼
]

# 动态扩展：从 PROVIDERS_DIR 加载自定义插件
PROVIDERS_DIR = os.getenv("PROVIDERS_DIR", "")


def _discover_providers() -> list[str]:
    """发现所有可用的提供商模块"""
    modules = list(BUILTIN_PROVIDERS)

    # 加载自定义插件目录
    if PROVIDERS_DIR and Path(PROVIDERS_DIR).exists():
        for f in Path(PROVIDERS_DIR).glob("*.py"):
            if f.name.startswith("_"):
                continue
            # 转为模块路径
            module_name = f"custom_providers.{f.stem}"
            modules.append(module_name)

    return modules


def _load_provider_class(module_path: str) -> type[BaseProvider] | None:
    """从模块中加载 Provider 类"""
    try:
        module = importlib.import_module(module_path)
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseProvider) and obj is not BaseProvider:
                return obj
    except Exception as e:
        logger.debug(f"加载提供商模块 {module_path} 失败: {e}")
    return None


def get_available_providers() -> list[type[BaseProvider]]:
    """获取所有已配置的提供商类"""
    providers = []
    for module_path in _discover_providers():
        cls = _load_provider_class(module_path)
        if cls and cls.is_configured():
            providers.append(cls)
            logger.info(f"[ProviderRegistry] 发现已配置提供商: {cls.name}")

    if not providers:
        logger.warning("[ProviderRegistry] 未发现任何已配置的图片生成提供商")

    return providers


def get_provider(name: str | None = None) -> BaseProvider | None:
    """
    获取指定名称的提供商实例
    如果 name 为 None，返回第一个已配置的提供商
    """
    available = get_available_providers()

    if not available:
        return None

    if name:
        for cls in available:
            if cls.name == name:
                return cls()
        logger.warning(f"[ProviderRegistry] 未找到提供商 '{name}'，使用默认")

    # 返回第一个（按优先级）
    return available[0]()


def list_configured_providers() -> list[dict]:
    """列出所有已配置的提供商信息"""
    result = []
    for module_path in _discover_providers():
        cls = _load_provider_class(module_path)
        if cls:
            result.append({
                "name": cls.name,
                "configured": cls.is_configured(),
                "required_keys": cls.required_keys,
            })
    return result
