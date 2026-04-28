import base64
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import cache_reference_image, get_recent_reference_image
from feishu_api import FeishuAPI
from providers.lieniao import LieniaoProvider


def test_cache_and_get_recent_reference_image(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    img = tmp_path / "ref.png"
    img.write_bytes(b"fake-image")

    cache_reference_image("chat_a", str(img), message_id="om_1", ttl_seconds=60)
    got = get_recent_reference_image("chat_a", ttl_seconds=60)

    assert got == str(img)


def test_download_message_resource_uses_message_resource_endpoint():
    api = FeishuAPI()
    api._token = "t-test"
    api._token_expires = 9999999999

    class Resp:
        content = b"image-bytes"
        def raise_for_status(self):
            return None

    with patch("feishu_api.requests.get", return_value=Resp()) as mock_get:
        data = api.download_message_resource("om_x", "img_x", "image")

    assert data == b"image-bytes"
    url = mock_get.call_args.args[0]
    assert url.endswith("/im/v1/messages/om_x/resources/img_x")
    assert mock_get.call_args.kwargs["params"] == {"type": "image"}


def test_upload_image_sends_required_message_image_type():
    api = FeishuAPI()
    api._token = "t-test"
    api._token_expires = 9999999999

    class Resp:
        text = '{"code":0,"data":{"image_key":"img_ok"}}'
        def raise_for_status(self):
            return None
        def json(self):
            return {"code": 0, "data": {"image_key": "img_ok"}}

    with patch("feishu_api.requests.post", return_value=Resp()) as mock_post:
        image_key = api.upload_image(b"fake-image")

    assert image_key == "img_ok"
    files = mock_post.call_args.kwargs["files"]
    assert files["image_type"] == (None, "message")
    assert "image" in files


def test_gemini_payload_contains_reference_image(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 20)
    captured = {}

    class Resp:
        status_code = 200
        def json(self):
            return {
                "candidates": [{
                    "content": {
                        "parts": [{
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": base64.b64encode(b"generated" * 50).decode("utf-8"),
                            }
                        }]
                    }
                }]
            }
        def raise_for_status(self):
            pass

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["payload"] = json
        captured["url"] = url
        return Resp()

    gen = LieniaoProvider()
    gen.gemini_api_key = "sk-test"
    gen.output_dir = tmp_path

    with patch("providers.lieniao.requests.post", side_effect=fake_post):
        result = gen.generate("参考这张图生成白底图", "square", reference_images=[str(ref)])

    assert result.success is True
    parts = captured["payload"]["contents"][0]["parts"]
    assert any(("inlineData" in p or "inline_data" in p) for p in parts)
    inline = next((p.get("inlineData") or p.get("inline_data")) for p in parts if ("inlineData" in p or "inline_data" in p))
    assert (inline.get("mimeType") or inline.get("mime_type")) == "image/png"
    assert inline["data"] == base64.b64encode(ref.read_bytes()).decode("utf-8")


if __name__ == "__main__":
    test_cache_and_get_recent_reference_image(Path("/tmp/feishu_ref_test"))
    test_download_message_resource_uses_message_resource_endpoint()
    test_upload_image_sends_required_message_image_type()
    test_gemini_payload_contains_reference_image(Path("/tmp/feishu_ref_test"))
    print("OK reference image tests passed")
