import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from providers.lieniao import LieniaoProvider
from providers import BaseProvider


def test_normalize_ratio():
    gen = LieniaoProvider()
    assert gen._normalize_ratio("portrait") == "9:16"
    assert gen._normalize_ratio("landscape") == "16:9"
    assert gen._normalize_ratio("square") == "1:1"
    # 未知比例 fallback 到默认 portrait
    assert gen._normalize_ratio("3:4") == "9:16"
    print("OK _normalize_ratio")


def test_size_from_ratio():
    gen = LieniaoProvider()
    assert gen._size_from_ratio("portrait") == "1024x1792"
    assert gen._size_from_ratio("landscape") == "1792x1024"
    assert gen._size_from_ratio("square") == "1024x1024"
    print("OK _size_from_ratio")


def test_select_backend():
    gen = LieniaoProvider()
    assert gen._select_backend("生成一张猫图") == "gemini"
    assert gen._select_backend("用烈鸟 Gemini 生成") == "gemini"
    assert gen._select_backend("用 image2 生成") == "image2"
    assert gen._select_backend("用 gpt-image-2-medium 生成") == "image2"
    assert gen._select_backend("gpt-image-2 商品图") == "image2"
    assert gen._select_backend("openai 风格头像") == "image2"
    assert gen._select_backend("调用 gpt image 2 生成") == "image2"
    print("OK _select_backend")


def test_image2_with_reference_uses_edits_endpoint():
    """prompt 显式要求 image2 且有参考图时，必须走 /v1/images/edits"""
    import base64
    import tempfile
    from unittest.mock import patch

    gen = LieniaoProvider()
    gen.image2_api_key = "sk-test"
    gen.output_dir = Path(tempfile.gettempdir()) / "feishu_image2_edit_out"
    gen.output_dir.mkdir(exist_ok=True)

    ref = Path(tempfile.gettempdir()) / "feishu_image2_edit_ref.png"
    ref.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 200)

    captured = {}

    class FakeResp:
        status_code = 200
        def json(self):
            return {"data": [{"b64_json": base64.b64encode(b"fake-generated-image" * 50).decode()}]}
        def raise_for_status(self):
            pass

    def fake_post(url, data=None, files=None, headers=None, timeout=None, json=None):
        captured["url"] = url
        captured["data"] = data
        captured["files_keys"] = sorted(files.keys()) if isinstance(files, dict) else None
        captured["headers"] = headers
        return FakeResp()

    with patch("providers.lieniao.requests.post", side_effect=fake_post):
        result = gen.generate("调用 gpt image 2 生成小红书封面", "portrait", reference_images=[str(ref)])

    assert result.success is True, f"期望成功，实际: {result.error}"
    assert "gpt-image-2-all" in result.tool_used
    assert result.image_path is not None
    assert "/v1/images/edits" in captured["url"], f"期望 edits 端点，实际: {captured['url']}"
    assert captured["data"]["model"] == "gpt-image-2-all"
    assert captured["data"]["response_format"] == "b64_json"
    assert captured["data"]["size"] == "1024x1792"
    assert "image" in (captured["files_keys"] or [])
    # headers 不应包含 application/json，让 requests 自动生成 multipart boundary
    assert "Content-Type" not in (captured.get("headers") or {})
    print("OK image2_with_reference_uses_edits_endpoint")


def test_gemini_with_reference_uses_gemini():
    """prompt 未要求 image2 且有参考图时，默认 backend gemini 应走 Gemini"""
    import base64
    import tempfile
    from unittest.mock import patch

    gen = LieniaoProvider()
    gen.gemini_api_key = "sk-test"
    gen.output_dir = Path(tempfile.gettempdir()) / "feishu_gemini_ref_out"
    gen.output_dir.mkdir(exist_ok=True)

    ref = Path(tempfile.gettempdir()) / "feishu_gemini_ref.png"
    ref.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 200)

    captured = {}

    class FakeResp:
        status_code = 200
        def json(self):
            return {
                "candidates": [{
                    "content": {
                        "parts": [{
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": base64.b64encode(b"fake-generated-image" * 50).decode(),
                            }
                        }]
                    }
                }]
            }
        def raise_for_status(self):
            pass

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["payload"] = json
        return FakeResp()

    with patch("providers.lieniao.requests.post", side_effect=fake_post):
        result = gen.generate("参考这张图生成白底图", "square", reference_images=[str(ref)])

    assert result.success is True, f"期望成功，实际: {result.error}"
    assert "gemini-3-pro-image-preview" in result.tool_used
    assert "generateContent" in captured["url"]
    parts = captured["payload"]["contents"][0]["parts"]
    assert any(("inlineData" in p or "inline_data" in p) for p in parts)
    print("OK gemini_with_reference_uses_gemini")


def test_default_image2_with_reference_uses_edits():
    """默认 backend 为 image2 且无显式关键词，有参考图时也应走 edits"""
    import base64
    import tempfile
    from unittest.mock import patch

    gen = LieniaoProvider()
    gen.default_backend = "image2"
    gen.image2_api_key = "sk-test"
    gen.output_dir = Path(tempfile.gettempdir()) / "feishu_default_image2_ref_out"
    gen.output_dir.mkdir(exist_ok=True)

    ref = Path(tempfile.gettempdir()) / "feishu_default_image2_ref.png"
    ref.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 200)

    captured = {}

    class FakeResp:
        status_code = 200
        def json(self):
            return {"data": [{"b64_json": base64.b64encode(b"fake-generated-image" * 50).decode()}]}
        def raise_for_status(self):
            pass

    def fake_post(url, data=None, files=None, headers=None, timeout=None, json=None):
        captured["url"] = url
        return FakeResp()

    with patch("providers.lieniao.requests.post", side_effect=fake_post):
        result = gen.generate("按这张图改成白色极简风", "square", reference_images=[str(ref)])

    assert result.success is True
    assert "/v1/images/edits" in captured["url"]
    print("OK default_image2_with_reference_uses_edits")


def test_separate_keys_attributes():
    gen = LieniaoProvider()
    assert hasattr(gen, "gemini_api_key")
    assert hasattr(gen, "image2_api_key")
    print("OK separate_keys_attributes")


def test_is_configured_detects_env():
    """测试 is_configured 能根据环境变量检测配置状态（不依赖真实 key）"""
    import os

    # 先清除所有相关环境变量
    for key in ("LIENIAO_API_KEY", "LIENIAO_GEMINI_API_KEY", "LIENIAO_IMAGE2_API_KEY"):
        os.environ.pop(key, None)

    assert LieniaoProvider.is_configured() is False

    os.environ["LIENIAO_GEMINI_API_KEY"] = "sk-test"
    assert LieniaoProvider.is_configured() is True

    os.environ.pop("LIENIAO_GEMINI_API_KEY", None)
    os.environ["LIENIAO_IMAGE2_API_KEY"] = "sk-test"
    assert LieniaoProvider.is_configured() is True

    os.environ.pop("LIENIAO_IMAGE2_API_KEY", None)
    assert LieniaoProvider.is_configured() is False
    print("OK is_configured")


def test_generate_with_mock_image2():
    """用 mock 测试 image2 text-to-image，不调用真实 API"""
    import base64
    from unittest.mock import patch

    gen = LieniaoProvider()
    gen.image2_api_key = "sk-test"
    gen.output_dir = Path("/tmp/feishu_test_image2")
    gen.output_dir.mkdir(parents=True, exist_ok=True)

    fake_image = b"fake-image-data" * 50  # 确保 base64 长度 > 100

    class FakeResp:
        status_code = 200
        def json(self):
            return {
                "data": [{
                    "b64_json": base64.b64encode(fake_image).decode("utf-8")
                }]
            }
        def raise_for_status(self):
            pass

    with patch("providers.lieniao.requests.post", return_value=FakeResp()):
        result = gen.generate("image2 测试图片", "square")

    assert result.success is True
    assert result.image_path is not None
    print("OK mock image2 generate")


def test_generate_with_mock_gemini():
    """用 mock 测试 gemini text-to-image，不调用真实 API"""
    import base64
    from unittest.mock import patch

    gen = LieniaoProvider()
    gen.gemini_api_key = "sk-test"
    gen.output_dir = Path("/tmp/feishu_test_gemini")
    gen.output_dir.mkdir(parents=True, exist_ok=True)

    fake_image = b"fake-image-data" * 50  # 确保 base64 长度 > 100

    class FakeResp:
        status_code = 200
        def json(self):
            return {
                "candidates": [{
                    "content": {
                        "parts": [{
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": base64.b64encode(fake_image).decode("utf-8")
                            }
                        }]
                    }
                }]
            }
        def raise_for_status(self):
            pass

    with patch("providers.lieniao.requests.post", return_value=FakeResp()):
        result = gen.generate("测试图片", "portrait")

    assert result.success is True
    assert result.image_path is not None
    print("OK mock gemini generate")


if __name__ == "__main__":
    test_normalize_ratio()
    test_size_from_ratio()
    test_select_backend()
    test_image2_with_reference_uses_edits_endpoint()
    test_gemini_with_reference_uses_gemini()
    test_default_image2_with_reference_uses_edits()
    test_separate_keys_attributes()
    test_is_configured_detects_env()
    test_generate_with_mock_image2()
    test_generate_with_mock_gemini()
    print("\nOK all lieniao provider tests passed")
