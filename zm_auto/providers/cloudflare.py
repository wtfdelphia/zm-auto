"""CloudflareTempMailProvider implementation."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from typing import Any

from curl_cffi import requests as curl_requests

from .base import (
    BaseMailProvider,
    _extract_content,
    _message_matches_email,
    _next_domain,
    _parse_received_at,
    _random_mailbox_name,
)


class CloudflareTempMailProvider(BaseMailProvider):
    type = "cloudflare_temp_email"
    name = "cloudflare_temp_email"

    def __init__(self, entry: dict, conf: dict, proxy: str = ""):
        super().__init__(conf, str(entry.get("provider_ref") or ""))
        self.api_base = str(entry["api_base"]).rstrip("/")
        self.admin_password = str(entry["admin_password"]).strip()
        self.domain = entry.get("domain") or []
        self.session: Any = curl_requests.Session(impersonate="chrome")
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

    def _request(self, method, path, headers=None, params=None, payload=None, expected=(200,)):
        resp = self.session.request(
            method.upper(),
            f"{self.api_base}{path}",
            headers={"Content-Type": "application/json", "User-Agent": self.conf["user_agent"], **(headers or {})},
            params=params,
            json=payload,
            timeout=self.conf["request_timeout"],
            verify=False,
        )
        if resp.status_code not in expected:
            raise RuntimeError(
                f"CloudflareTempMail 请求失败: {method} {path}, HTTP {resp.status_code}, body={resp.text[:300]}"
            )
        return {} if resp.status_code == 204 else resp.json()

    def create_mailbox(self, username: str | None = None) -> dict[str, Any]:
        data = self._request(
            "POST",
            "/admin/new_address",
            headers={"x-admin-auth": self.admin_password},
            payload={
                "enablePrefix": True,
                "name": username or _random_mailbox_name(),
                "domain": _next_domain(self.domain),
            },
        )
        address = str(data.get("address") or "").strip()
        token = str(data.get("jwt") or "").strip()
        if not address or not token:
            raise RuntimeError("CloudflareTempMail 缺少 address 或 jwt")
        return {
            "provider": self.name,
            "provider_ref": self.provider_ref,
            "address": address,
            "token": token,
        }

    def _fetch_messages(self, mailbox: dict[str, Any], parsed: bool = False) -> list[dict]:
        """Fetch messages from API. If parsed=True, use /api/parsed_mails (decoded subject/text/html)."""
        path = "/api/parsed_mails" if parsed else "/api/mails"
        data = self._request(
            "GET",
            path,
            headers={"Authorization": f"Bearer {mailbox['token']}"},
            params={"limit": 10, "offset": 0},
        )
        raw = list(data.get("results") or []) if isinstance(data, dict) else data if isinstance(data, list) else []
        return [item for item in raw if isinstance(item, dict)]

    def fetch_latest_message(self, mailbox: dict[str, Any]) -> dict[str, Any] | None:
        # Try parsed endpoint first (cleaner: decoded subject, text, html)
        for parsed in (True, False):
            raw = self._fetch_messages(mailbox, parsed=parsed)
            if raw:
                logger.debug(f"  [DEBUG] fetch_latest_message(parsed={parsed}): {len(raw)} 条, keys={list(raw[0].keys())}")
            messages = [
                item for item in raw
                if _message_matches_email(item, str(mailbox.get("address") or ""))
            ]
            if not messages:
                continue
            item = messages[0]
            if parsed:
                # parsed endpoint already has decoded subject/text/html
                text_content = str(item.get("text") or "")
                html_content = str(item.get("html") or "")
                subject = str(item.get("subject") or "")
                sender = str(item.get("sender") or item.get("source") or "")
            else:
                text_content, html_content = _extract_content(item)
                subject = str(item.get("subject") or "")
                sender = item.get("from") or item.get("source") or item.get("sender") or ""
            if isinstance(sender, dict):
                sender = sender.get("address") or sender.get("email") or sender.get("name") or ""
            logger.debug(f"  [DEBUG] subject={subject[:80]!r}")
            logger.debug(f"  [DEBUG] text={text_content[:200]!r}")
            logger.debug(f"  [DEBUG] html={html_content[:200]!r}")
            return {
                "provider": self.name,
                "mailbox": mailbox["address"],
                "message_id": str(item.get("id") or item.get("_id") or ""),
                "subject": subject,
                "sender": str(sender),
                "text_content": text_content,
                "html_content": html_content,
                "received_at": _parse_received_at(
                    item.get("createdAt") or item.get("created_at") or item.get("receivedAt") or item.get("date") or item.get("timestamp")
                ),
                "raw": item,
            }
        return None

    def close(self) -> None:
        self.session.close()
