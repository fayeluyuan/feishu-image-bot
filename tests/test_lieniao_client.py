import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lieniao_client import LieniaoImageGenerator, normalize_ratio, size_from_ratio


def test_normalize_ratio():
    assert normalize_ratio("portrait") == "9:16"
    assert normalize_ratio("landscape") == "16:9"
    assert normalize_ratio("square") == "1:1"
    assert normalize_ratio("3:4") == "3:4"


def test_size_from_ratio():
    assert size_from_ratio("portrait") == "1024x1792"
    assert size_from_ratio("landscape") == "1792x1024"
    assert size_from_ratio("square") == "1024x1024"


def test_select_backend():
    gen = LieniaoImageGenerator()
    assert gen.select_backend("生成一张猫图") == "gemini"
    assert gen.select_backend("用烈鸟 Gemini 生成") == "gemini"
    assert gen.select_backend("用 image2 生成") == "image2"
    assert gen.select_backend("用 gpt-image-2-medium 生成") == "image2"


if __name__ == "__main__":
    test_normalize_ratio()
    test_size_from_ratio()
    test_select_backend()
    print("OK lieniao_client tests passed")


def test_separate_keys_attributes():
    gen = LieniaoImageGenerator()
    assert hasattr(gen, "gemini_api_key")
    assert hasattr(gen, "image2_api_key")
