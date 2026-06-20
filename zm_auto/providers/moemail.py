"""MoEmailProvider implementation."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from curl_cffi import requests as curl_requests

from .base import (
    BaseMailProvider,
    _extract_content,
    _next_domain,
    _parse_received_at,
    _random_mailbox_name,
)


class MoEmailProvider(BaseMailProvider):
    type = "moemail"
    name = "moemail"

    def __init__(self, entry: dict, conf: dict, proxy: str = ""):
        super().__init__(conf, str(entry.get("provider_ref") or ""))
        self.api_base = str(entry["api_base"]).rstrip("/")
        self.api_key = str(entry["api_key"]).strip()
        raw_domains = entry.get("domain") or []
        if isinstance(raw_domains, list):
            self.domain = [str(item).strip() for item in raw_domains if str(item).strip()]
        else:
            self.domain = [str(raw_domains).strip()] if str(raw_domains).strip() else []
        self.expiry_time = int(entry.get("expiry_time") or 0)
        self.session: Any = curl_requests.Session(impersonate="chrome")
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

    def _request(self, method, path, params=None, payload=None, expected=(200,)):
        resp = self.session.request(
            method.upper(),
            f"{self.api_base}{path}",
            headers={"X-API-Key": self.api_key, "Content-Type": "application/json", "User-Agent": self.conf["user_agent"]},
            params=params,
            json=payload,
            timeout=self.conf["request_timeout"],
            verify=False,
        )
        if resp.status_code not in expected:
            raise RuntimeError(
                f"MoEmail 请求失败: {method} {path}, HTTP {resp.status_code}, body={resp.text[:300]}"
            )
        data = resp.json()
        if not isinstance(data, dict):
            raise RuntimeError(f"MoEmail {method} {path} 返回结构不是对象")
        return data

    def create_mailbox(self, username: str | None = None) -> dict[str, Any]:
        data = self._request(
            "POST",
            "/api/emails/generate",
            payload={
                "name": username or _random_mailbox_name(),
                "expiryTime": self.expiry_time,
                "domain": _next_domain(self.domain),
            },
            expected=(200, 201),
        )
        address = str(data.get("email") or "").strip()
        email_id = str(data.get("id") or data.get("email_id") or "").strip()
        if not address or not email_id:
            raise RuntimeError("MoEmail 缺少 email 或 id")
        return {
            "provider": self.name,
            "provider_ref": self.provider_ref,
            "address": address,
            "email_id": email_id,
        }

    def fetch_latest_message(self, mailbox: dict[str, Any]) -> dict[str, Any] | None:
        email_id = str(mailbox.get("email_id") or "").strip()
        if not email_id:
            raise RuntimeError("MoEmail 缺少 email_id")
        data = self._request("GET", f"/api/emails/{email_id}")
        items = data.get("messages") or []
        messages = [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []
        if not messages:
            return None
        _, item = max(
            enumerate(messages),
            key=lambda pair: (
                (
                    _parse_received_at(
                        pair[1].get("createdAt")
                        or pair[1].get("created_at")
                        or pair[1].get("receivedAt")
                        or pair[1].get("date")
                        or pair[1].get("timestamp")
                    )
                    or datetime.fromtimestamp(0, tz=timezone.utc)
                ).timestamp(),
                pair[0],
            ),
        )
        message_id = str(item.get("id") or item.get("message_id") or item.get("_id") or "").strip()
        detail = self._request("GET", f"/api/emails/{email_id}/{message_id}") if message_id else {"message": item}
        raw_message = detail.get("message") if isinstance(detail, dict) else None
        if isinstance(raw_message, dict):
            message: dict[str, Any] = raw_message
        else:
            message = item
        text_content, html_content = _extract_content(message)
        sender = message.get("from") or message.get("sender") or ""
        if isinstance(sender, dict):
            sender = sender.get("address") or sender.get("email") or sender.get("name") or ""
        return {
            "provider": self.name,
            "mailbox": mailbox["address"],
            "message_id": message_id,
            "subject": str(message.get("subject") or item.get("subject") or ""),
            "sender": str(sender),
            "text_content": text_content,
            "html_content": html_content,
            "received_at": _parse_received_at(
                message.get("createdAt")
                or message.get("created_at")
                or message.get("receivedAt")
                or message.get("date")
                or message.get("timestamp")
                or item.get("createdAt")
                or item.get("created_at")
                or item.get("receivedAt")
                or item.get("date")
                or item.get("timestamp")
            ),
            "raw": detail,
        }

    def close(self) -> None:
        self.session.close()
