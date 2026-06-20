from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import random

from datetime import datetime, timezone

"""TempMailLolProvider implementation."""

from typing import Any

import requests

from .base import (
    BaseMailProvider,
    _extract_content,
    _parse_received_at,
    _random_mailbox_name,
    _random_subdomain_label,
)


class TempMailLolProvider(BaseMailProvider):
    type = "tempmail_lol"
    name = "tempmail_lol"

    def __init__(self, entry: dict, conf: dict, proxy: str = ""):
        super().__init__(conf, str(entry.get("provider_ref") or ""))
        self.api_key = str(entry.get("api_key") or "").strip()
        self.domain = [str(item).strip() for item in (entry.get("domain") or []) if str(item).strip()]
        self.session = requests.Session()
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
        self.session.trust_env = False
        self.session.headers.update(
            {"User-Agent": conf["user_agent"], "Accept": "application/json", "Content-Type": "application/json"}
        )
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"

    @staticmethod
    def _resolve_domain(domain: str) -> tuple[str, bool]:
        text = str(domain or "").strip().lower()
        if text.startswith("*.") and len(text) > 2:
            return f"{_random_subdomain_label()}.{text[2:]}", True
        return text, False

    def _request(self, method, path, params=None, payload=None, expected=(200,)):
        resp = self.session.request(
            method.upper(),
            f"https://api.tempmail.lol/v2{path}",
            params=params,
            json=payload,
            timeout=self.conf["request_timeout"],
            verify=False,
        )
        if resp.status_code not in expected:
            raise RuntimeError(
                f"TempMail.lol 请求失败: {method} {path}, HTTP {resp.status_code}, body={resp.text[:300]}"
            )
        data = resp.json()
        if not isinstance(data, dict):
            raise RuntimeError(f"TempMail.lol {method} {path} 返回结构不是对象")
        return data

    def create_mailbox(self, username: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.domain:
            domain, force_random_prefix = self._resolve_domain(random.choice(self.domain))
            payload["domain"] = domain
            if force_random_prefix:
                payload["prefix"] = _random_mailbox_name()
        if username and "prefix" not in payload:
            payload["prefix"] = username
        data = self._request("POST", "/inbox/create", payload=payload, expected=(200, 201))
        address = str(data.get("address") or "").strip()
        token = str(data.get("token") or "").strip()
        if not address or not token:
            raise RuntimeError("TempMail.lol 缺少 address 或 token")
        return {
            "provider": self.name,
            "provider_ref": self.provider_ref,
            "address": address,
            "token": token,
        }

    def fetch_latest_message(self, mailbox: dict[str, Any]) -> dict[str, Any] | None:
        data = self._request("GET", "/inbox", params={"token": mailbox["token"]})
        items = data.get("emails") or data.get("messages") or []
        messages = [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []
        if not messages:
            return None
        item = max(
            messages,
            key=lambda value: (
                (
                    _parse_received_at(
                        value.get("created_at")
                        or value.get("createdAt")
                        or value.get("date")
                        or value.get("received_at")
                        or value.get("timestamp")
                    )
                    or datetime.fromtimestamp(0, tz=timezone.utc)
                ).timestamp(),
                str(value.get("id") or value.get("token") or ""),
            ),
        )
        text_content, html_content = _extract_content(item)
        logger.debug(f"  [DEBUG] _extract_content: text={text_content[:200]!r}")
        logger.debug(f"  [DEBUG] _extract_content: html={html_content[:200]!r}")
        return {
            "provider": self.name,
            "mailbox": mailbox["address"],
            "message_id": str(item.get("id") or item.get("token") or ""),
            "subject": str(item.get("subject") or ""),
            "sender": str(item.get("from") or item.get("from_address") or ""),
            "text_content": text_content,
            "html_content": html_content,
            "received_at": _parse_received_at(
                item.get("created_at")
                or item.get("createdAt")
                or item.get("date")
                or item.get("received_at")
                or item.get("timestamp")
            ),
            "raw": item,
        }

    def close(self) -> None:
        self.session.close()
