from __future__ import annotations

from datetime import datetime, timezone

"""YydsMailProvider implementation."""

from typing import Any

import requests

from .base import (
    BaseMailProvider,
    _extract_content,
    _next_domain,
    _parse_received_at,
    _random_mailbox_name,
)


class YydsMailProvider(BaseMailProvider):
    type = "yyds_mail"
    name = "yyds_mail"

    def __init__(self, entry: dict, conf: dict, proxy: str = ""):
        super().__init__(conf, str(entry.get("provider_ref") or ""))
        self.api_base = str(entry.get("api_base") or "https://maliapi.215.im/v1").rstrip("/")
        self.api_key = str(entry["api_key"]).strip()
        self.domain = [str(item).strip() for item in (entry.get("domain") or []) if str(item).strip()]
        self.subdomain = str(entry.get("subdomain") or "").strip()
        self.wildcard = bool(entry.get("wildcard"))
        self.session = requests.Session()
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
        self.session.trust_env = False
        self.session.headers.update(
            {"User-Agent": conf["user_agent"], "Accept": "application/json", "Content-Type": "application/json"}
        )

    def _request(self, method, path, token="", params=None, payload=None, expected=(200, 201, 204)):
        headers = {"Authorization": f"Bearer {token}"} if token else {"X-API-Key": self.api_key}
        resp = self.session.request(
            method.upper(),
            f"{self.api_base}{path}",
            headers=headers,
            params=params,
            json=payload,
            timeout=self.conf["request_timeout"],
            verify=False,
        )
        if resp.status_code not in expected:
            raise RuntimeError(
                f"YYDSMail 请求失败: {method} {path}, HTTP {resp.status_code}, body={resp.text[:300]}"
            )
        if resp.status_code == 204:
            return {}
        data = resp.json()
        if isinstance(data, dict) and data.get("success") is False:
            raise RuntimeError(f"YYDSMail 请求失败: {data.get('errorCode') or data.get('error')}")
        return data.get("data") if isinstance(data, dict) and isinstance(data.get("data"), (dict, list)) else data

    @staticmethod
    def _items(data):
        return data if isinstance(data, list) else data.get("items") or data.get("messages") or data.get("data") or []

    def create_mailbox(self, username: str | None = None) -> dict[str, Any]:
        payload = {"localPart": username or _random_mailbox_name()}
        if self.domain:
            payload["domain"] = _next_domain(self.domain)
        if self.subdomain:
            payload["subdomain"] = self.subdomain
        data = self._request("POST", "/accounts/wildcard" if self.wildcard else "/accounts", payload=payload)
        address = str(data.get("address") or data.get("email") or "").strip()
        token = str(
            data.get("token") or data.get("temp_token") or data.get("tempToken") or data.get("access_token") or ""
        ).strip()
        if not address or not token:
            raise RuntimeError("YYDSMail 缺少 address 或 token")
        return {
            "provider": self.name,
            "provider_ref": self.provider_ref,
            "address": address,
            "token": token,
            "account_id": str(data.get("id") or ""),
        }

    def fetch_latest_message(self, mailbox: dict[str, Any]) -> dict[str, Any] | None:
        data = self._request("GET", "/messages", token=str(mailbox.get("token") or ""), params={"address": mailbox["address"]})
        messages = [item for item in self._items(data) if isinstance(item, dict)]
        if not messages:
            return None
        item = max(
            messages,
            key=lambda value: (
                (
                    _parse_received_at(
                        value.get("createdAt")
                        or value.get("created_at")
                        or value.get("receivedAt")
                        or value.get("date")
                        or value.get("timestamp")
                    )
                    or datetime.fromtimestamp(0, tz=timezone.utc)
                ).timestamp(),
                str(value.get("id") or ""),
            ),
        )
        message_id = str(item.get("id") or item.get("message_id") or "").strip()
        if message_id:
            item = self._request("GET", f"/messages/{message_id}", token=str(mailbox.get("token") or ""), params={"address": mailbox["address"]})
        text_content, html_content = _extract_content(item)
        sender = item.get("from") or item.get("source") or item.get("sender") or ""
        if isinstance(sender, dict):
            sender = sender.get("address") or sender.get("email") or sender.get("name") or ""
        return {
            "provider": self.name,
            "mailbox": mailbox["address"],
            "message_id": message_id,
            "subject": str(item.get("subject") or ""),
            "sender": str(sender),
            "text_content": text_content,
            "html_content": html_content,
            "received_at": _parse_received_at(
                item.get("createdAt")
                or item.get("created_at")
                or item.get("receivedAt")
                or item.get("date")
                or item.get("timestamp")
            ),
            "raw": item,
        }

    def close(self) -> None:
        self.session.close()
