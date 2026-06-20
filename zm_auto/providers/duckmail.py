"""DuckMailProvider implementation."""
from __future__ import annotations

import random
import string
from typing import Any

import requests

from .base import (
    BaseMailProvider,
    _parse_received_at,
    _random_mailbox_name,
)


class DuckMailProvider(BaseMailProvider):
    type = "duckmail"
    name = "duckmail"

    def __init__(self, entry: dict, conf: dict, proxy: str = ""):
        super().__init__(conf, str(entry.get("provider_ref") or ""))
        self.api_key = str(entry["api_key"]).strip()
        self.default_domain = str(entry.get("default_domain") or "duckmail.sbs").strip() or "duckmail.sbs"
        self.session = requests.Session()
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
        self.session.trust_env = False
        self.session.headers.update(
            {"User-Agent": conf["user_agent"], "Accept": "application/json", "Content-Type": "application/json"}
        )

    def _request(self, method, path, token="", use_api_key=False, params=None, payload=None, expected=(200, 201, 204)):
        headers = (
            {"Authorization": f"Bearer {self.api_key if use_api_key else token}"} if use_api_key or token else {}
        )
        resp = self.session.request(
            method.upper(),
            f"https://api.duckmail.sbs{path}",
            headers=headers,
            params=params,
            json=payload,
            timeout=self.conf["request_timeout"],
            verify=False,
        )
        if resp.status_code not in expected:
            raise RuntimeError(
                f"DuckMail 请求失败: {method} {path}, HTTP {resp.status_code}, body={resp.text[:300]}"
            )
        return {} if resp.status_code == 204 else resp.json()

    @staticmethod
    def _items(data):
        return data if isinstance(data, list) else data.get("hydra:member") or data.get("member") or data.get("data") or []

    def create_mailbox(self, username: str | None = None) -> dict[str, Any]:
        password = "".join(random.choices(string.ascii_letters + string.digits, k=12))
        address = f"{username or _random_mailbox_name()}@{self.default_domain}"
        payload = {"address": address, "password": password}
        account = self._request("POST", "/accounts", use_api_key=True, payload=payload)
        token_data = self._request("POST", "/token", use_api_key=True, payload=payload)
        return {
            "provider": self.name,
            "provider_ref": self.provider_ref,
            "address": address,
            "token": str(token_data.get("token") or ""),
            "password": password,
            "account_id": str(account.get("id") or ""),
        }

    def fetch_latest_message(self, mailbox: dict[str, Any]) -> dict[str, Any] | None:
        data = self._request("GET", "/messages", token=str(mailbox.get("token") or ""), params={"page": 1})
        items = self._items(data)
        if not items:
            return None
        item = items[0]
        message_id = str(item.get("id") or item.get("@id") or "").replace("/messages/", "")
        if message_id:
            item = self._request("GET", f"/messages/{message_id}", token=str(mailbox.get("token") or ""))
        sender = item.get("from") or ""
        if isinstance(sender, dict):
            sender = sender.get("address") or sender.get("name") or ""
        html_content = item.get("html") or ""
        if isinstance(html_content, list):
            html_content = "".join(str(value) for value in html_content)
        return {
            "provider": self.name,
            "mailbox": mailbox["address"],
            "message_id": message_id,
            "subject": str(item.get("subject") or ""),
            "sender": str(sender),
            "text_content": str(item.get("text") or item.get("text_content") or ""),
            "html_content": str(html_content),
            "received_at": _parse_received_at(
                item.get("createdAt") or item.get("created_at") or item.get("receivedAt") or item.get("date")
            ),
            "raw": item,
        }

    def close(self) -> None:
        self.session.close()
