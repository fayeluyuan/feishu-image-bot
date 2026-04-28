import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import parse_size_or_ratio, postprocess_image


def test_parse_size_or_ratio():
    """测试尺寸/比例解析"""
    # 9:16
    r = parse_size_or_ratio("帮我生成一张 9:16 的图")
    assert r["aspect_ratio"] == "portrait"
    assert r["target_size"] is None
    print(f"OK 9:16 -> {r}")

    # 16:9
    r = parse_size_or_ratio("做一个 16:9 的 banner")
    assert r["aspect_ratio"] == "landscape"
    assert r["target_size"] is None
    print(f"OK 16:9 -> {r}")

    # 750x1200
    r = parse_size_or_ratio("生成 750x1200 的电商长图")
    assert r["aspect_ratio"] == "portrait"
    assert r["target_size"] == [750, 1200]
    print(f"OK 750x1200 -> {r}")

    # PPT
    r = parse_size_or_ratio("做一张 PPT 配图")
    assert r["aspect_ratio"] == "landscape"
    assert r["target_size"] is None
    print(f"OK PPT -> {r}")

    # 淘宝详情页
    r = parse_size_or_ratio("淘宝详情页，一只猫")
    assert r["aspect_ratio"] == "portrait"
    assert r["target_size"] is None
    print(f"OK 淘宝详情页 -> {r}")

    # 方图
    r = parse_size_or_ratio("方图头像")
    assert r["aspect_ratio"] == "square"
    print(f"OK 方图 -> {r}")

    # 1:1
    r = parse_size_or_ratio("1:1 商品主图")
    assert r["aspect_ratio"] == "square"
    print(f"OK 1:1 -> {r}")

    # 小红书
    r = parse_size_or_ratio("小红书风格穿搭图")
    assert r["aspect_ratio"] == "portrait"
    print(f"OK 小红书 -> {r}")

    # 1024x1536
    r = parse_size_or_ratio("1024x1536 竖版")
    assert r["target_size"] == [1024, 1536]
    assert r["aspect_ratio"] == "portrait"
    print(f"OK 1024x1536 -> {r}")

    # 1536x1024
    r = parse_size_or_ratio("1536x1024 横版")
    assert r["target_size"] == [1536, 1024]
    assert r["aspect_ratio"] == "landscape"
    print(f"OK 1536x1024 -> {r}")

    print("\nOK parse_size_or_ratio 全部测试通过")


def test_postprocess_image():
    """测试 Pillow 后处理"""
    from PIL import Image
    import tempfile
    import os

    # 创建一个测试图片
    tmp_dir = tempfile.gettempdir()
    src_path = os.path.join(tmp_dir, "test_src.png")
    dst_path = os.path.join(tmp_dir, "test_dst.png")

    img = Image.new("RGB", (1024, 1024), color=(100, 150, 200))
    img.save(src_path)

    # 后处理到 750x1200
    postprocess_image(src_path, [750, 1200], dst_path)

    with Image.open(dst_path) as result:
        assert result.size == (750, 1200), f"期望 (750, 1200)，实际 {result.size}"
        print(f"OK 后处理到 750x1200 成功: {result.size}")

    # 后处理到 1920x1080
    dst_path2 = os.path.join(tmp_dir, "test_dst2.png")
    postprocess_image(src_path, [1920, 1080], dst_path2)

    with Image.open(dst_path2) as result2:
        assert result2.size == (1920, 1080), f"期望 (1920, 1080)，实际 {result2.size}"
        print(f"OK 后处理到 1920x1080 成功: {result2.size}")

    # 清理
    for p in [src_path, dst_path, dst_path2]:
        if os.path.exists(p):
            os.remove(p)

    print("\nOK postprocess_image 全部测试通过")


if __name__ == "__main__":
    test_parse_size_or_ratio()
    test_postprocess_image()
    print("\nOK 所有 utils 测试通过")
