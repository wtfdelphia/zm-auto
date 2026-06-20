"""Site adapter base class.

借鉴 bb-browser site-adapter 设计：把站点特定路径和流程抽象为可插拔 adapter，
使 zm-auto 可以按站点扩展。
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseSiteAdapter(ABC):
    """Abstract base class for site-specific automation logic."""

    name: str = ""
    site_url: str = ""

    @abstractmethod
    def user_info_path(self) -> str:
        """Return API path for user info."""

    @abstractmethod
    def api_key_list_path(self) -> str:
        """Return API path for API key list."""

    @abstractmethod
    def api_key_page_path(self) -> str:
        """Return browser page path for API key management."""

    def register_endpoints(self) -> dict[str, str]:
        """Return a mapping of register-flow endpoint names to relative paths."""
        return {}
