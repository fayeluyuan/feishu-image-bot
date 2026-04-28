"""
飞书 API 封装
"""
import json
import logging
from io import BytesIO

import requests

from config import Config

logger = logging.getLogger(__name__)

FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"


class FeishuAPI:
    def __init__(self):
        self.app_id = Config.FEISHU_APP_ID
        self.app_secret = Config.FEISHU_APP_SECRET
        self._token: str | None = None
        self._token_expires: float = 0.0

    def _get_tenant_access_token(self) -> str:
        """获取 tenant_access_token（带缓存）"""
        import time

        if self._token and time.time() < self._token_expires - 60:
            return self._token

        url = f"{FEISHU_BASE_URL}/auth/v3/tenant_access_token/internal"
        resp = requests.post(url, json={
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"获取 token 失败: {data}")

        self._token = data["tenant_access_token"]
        self._token_expires = time.time() + data["expire"]
        logger.info("飞书 tenant_access_token 已刷新")
        return self._token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_tenant_access_token()}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def send_text(self, chat_id: str, text: str) -> dict:
        """发送纯文本消息"""
        url = f"{FEISHU_BASE_URL}/im/v1/messages?receive_id_type=chat_id"
        resp = requests.post(url, headers=self._headers(), json={
            "receive_id": chat_id,
            "msg_type": "text",
            "content": '{"text": "' + text.replace('"', '\\"') + '"}',
        }, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def send_image(self, chat_id: str, image_key: str) -> dict:
        """发送图片消息（需要先从本地上传获取 image_key）"""
        url = f"{FEISHU_BASE_URL}/im/v1/messages?receive_id_type=chat_id"
        resp = requests.post(url, headers=self._headers(), json={
            "receive_id": chat_id,
            "msg_type": "image",
            "content": f'{{"image_key": "{image_key}"}}',
        }, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def send_rich_text(self, chat_id: str, title: str, content: str, link: str = "") -> dict:
        """发送富文本消息（带标题、正文、链接）"""
        url = f"{FEISHU_BASE_URL}/im/v1/messages?receive_id_type=chat_id"

        post_content = {
            "zh_cn": {
                "title": title,
                "content": [
                    [{"tag": "text", "text": content}],
                ],
            }
        }
        if link:
            post_content["zh_cn"]["content"][0].append({
                "tag": "a",
                "text": "点击查看",
                "href": link,
            })

        resp = requests.post(url, headers=self._headers(), json={
            "receive_id": chat_id,
            "msg_type": "post",
            "content": json.dumps(post_content, ensure_ascii=False),
        }, timeout=30)
        resp.raise_for_status()
        return resp.json()


    def download_message_resource(self, message_id: str, file_key: str, resource_type: str = "image") -> bytes:
        """下载用户消息中的资源文件（图片/文件/音视频）。

        用户发到群里的图片不能用 /im/v1/images/{image_key} 下载；
        应使用消息资源接口，并且 message_id 和 file_key 必须匹配。
        """
        url = f"{FEISHU_BASE_URL}/im/v1/messages/{message_id}/resources/{file_key}"
        headers = {"Authorization": f"Bearer {self._get_tenant_access_token()}"}
        resp = requests.get(url, headers=headers, params={"type": resource_type}, timeout=60)
        resp.raise_for_status()
        return resp.content

    def upload_image(self, image_data: bytes) -> str:
        """上传图片到飞书，返回 image_key"""
        url = f"{FEISHU_BASE_URL}/im/v1/images"
        headers = {"Authorization": f"Bearer {self._get_tenant_access_token()}"}
        files = {
            "image_type": (None, "message"),
            "image": ("image.png", BytesIO(image_data), "image/png"),
        }
        resp = requests.post(url, headers=headers, files=files, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"上传图片失败: {data}")
        return data["data"]["image_key"]

    def upload_file_to_drive(self, file_data: bytes, filename: str) -> dict:
        """
        上传文件到飞书云盘
        返回包含 file_token、url 等信息的 dict
        """
        url = f"{FEISHU_BASE_URL}/drive/v1/files/upload_all"
        headers = {"Authorization": f"Bearer {self._get_tenant_access_token()}"}

        files = {
            "file_name": (None, filename),
            "parent_type": (None, "explorer"),
            "size": (None, str(len(file_data))),
            "file": (filename, BytesIO(file_data), "application/octet-stream"),
        }

        resp = requests.post(url, headers=headers, files=files, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"上传文件到云盘失败: {data}")

        return data["data"]

    def reply_message(self, message_id: str, msg_type: str, content: str | dict) -> dict:
        """回复某条消息（用于在群聊中回复用户）"""
        url = f"{FEISHU_BASE_URL}/im/v1/messages/{message_id}/reply"
        if isinstance(content, dict):
            content_str = json.dumps(content, ensure_ascii=False)
        else:
            content_str = content

        resp = requests.post(url, headers=self._headers(), json={
            "msg_type": msg_type,
            "content": content_str,
        }, timeout=30)
        resp.raise_for_status()
        return resp.json()


# 全局单例
feishu_api = FeishuAPI()
