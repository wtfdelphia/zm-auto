"""Zenmux site adapter."""
from __future__ import annotations

from zm_auto.config import load_config

from .base import BaseSiteAdapter


class ZenmuxAdapter(BaseSiteAdapter):
    """Adapter for the zenmux target site."""

    name = "zenmux"

    @property
    def site_url(self) -> str:  # type: ignore[override]
        return str(load_config().site_url).rstrip("/")

    def user_info_path(self) -> str:
        return "/api/user/info"

    def api_key_list_path(self) -> str:
        return "/api/api_key/list"

    def api_key_page_path(self) -> str:
        return "/platform/pay-as-you-go"

    def register_endpoints(self) -> dict[str, str]:
        return {
            "send_code": "/api/auth/email/send-code",
            "verify_code": "/api/auth/email/verify-code",
            "create_key": "/api/api_key",
        }
