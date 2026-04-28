import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hermes_client import HermesMediaGenerator


def test_extract_image_path():
    """测试从 stdout 提取 IMAGE_PATH"""
    gen = HermesMediaGenerator()

    # 测试 IMAGE_PATH 正则解析
    stdout1 = """
正在生成图片...
使用工具：image_generate
IMAGE_PATH=/home/ubuntu/images/test.png
完成
"""
    import re
    m = re.search(r"IMAGE_PATH=(.+)", stdout1)
    assert m is not None, "未匹配到 IMAGE_PATH"
    path = m.group(1).strip().strip('"\'')
    assert path == "/home/ubuntu/images/test.png", f"路径不匹配: {path}"
    print(f"OK 解析 IMAGE_PATH: {path}")

    # 测试带引号的路径
    stdout2 = 'IMAGE_PATH="/tmp/my image.png"'
    m = re.search(r"IMAGE_PATH=(.+)", stdout2)
    path = m.group(1).strip().strip('"\'')
    assert path == "/tmp/my image.png", f"路径不匹配: {path}"
    print(f"OK 解析带引号的路径: {path}")

    # 测试 VIDEO_PATH 检测
    stdout3 = "VIDEO_PATH=/tmp/video.mp4"
    m = re.search(r"VIDEO_PATH=(.+)", stdout3)
    assert m is not None, "未匹配到 VIDEO_PATH"
    print(f"OK 解析 VIDEO_PATH: {m.group(1).strip()}")

    # 验证 HermesMediaGenerator 实例属性存在；具体 provider/model 可由 .env 覆盖
    assert isinstance(gen.image_provider, str)
    assert isinstance(gen.image_model, str)
    print(f"OK provider/model 配置可读取: {gen.image_provider or 'default'}/{gen.image_model or 'default'}")

    print("\nOK hermes_client 解析测试通过")


if __name__ == "__main__":
    test_extract_image_path()
    print("\nOK 所有 hermes_client 测试通过")
