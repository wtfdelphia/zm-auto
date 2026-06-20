"""GptMailProvider implementation."""
from __future__ import annotations

from typing import Any

import requests

from .base import (
    BaseMailProvider,
    _parse_received_at,
)


class GptMailProvider(BaseMailProvider):
    type = "gptmail"
    name = "gptmail"

    def __init__(self, entry: dict, conf: dict, proxy: str = ""):
        super().__init__(conf, str(entry.get("provider_ref") or ""))
        self.api_key = str(entry["api_key"]).strip()
        self.default_domain = str(entry.get("default_domain") or "").strip()
        self.session = requests.Session()
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
        self.session.trust_env = False
        self.session.headers.update(
            {
                "User-Agent": conf["user_agent"],
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
            }
        )

    def _request(self, method, path, params=None, payload=None):
        query = dict(params or {})
        resp = self.session.request(
            method.upper(),
            f"https://mail.chatgpt.org.uk{path}",
            params=query,
            json=payload,
            timeout=self.conf["request_timeout"],
            verify=False,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"GPTMail 请求失败: {method} {path}, HTTP {resp.status_code}, body={resp.text[:300]}"
            )
        data = resp.json()
        return data["data"] if isinstance(data, dict) and "data" in data else data

    def create_mailbox(self, username: str | None = None) -> dict[str, Any]:
        payload = {key: value for key, value in {"prefix": username, "domain": self.default_domain}.items() if value}
        data = self._request("POST" if payload else "GET", "/api/generate-email", payload=payload or None)
        return {
            "provider": self.name,
            "provider_ref": self.provider_ref,
            "address": str(data["email"]),
        }

    def fetch_latest_message(self, mailbox: dict[str, Any]) -> dict[str, Any] | None:
        data = self._request("GET", "/api/emails", params={"email": mailbox["address"]})
        emails = data if isinstance(data, list) else data.get("emails") or []
        if not emails:
            return None
        item = max(emails, key=lambda value: (float(value.get("timestamp") or 0), str(value.get("id") or "")))
        if item.get("id"):
            item = self._request("GET", f"/api/email/{item['id']}")
        return {
            "provider": self.name,
            "mailbox": mailbox["address"],
            "message_id": str(item.get("id") or ""),
            "subject": str(item.get("subject") or ""),
            "sender": str(item.get("from_address") or ""),
            "text_content": str(item.get("content") or ""),
            "html_content": str(item.get("html_content") or ""),
            "received_at": _parse_received_at(item.get("timestamp") or item.get("created_at")),
            "raw": item,
        }

    def close(self) -> None:
        self.session.close()
