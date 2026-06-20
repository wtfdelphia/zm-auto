"""Site adapter registry.

借鉴 provider 注册方式：通过 `BaseSiteAdapter.__subclasses__()` 自动发现 adapter。
"""
from __future__ import annotations

from typing import Any, cast
from urllib.parse import urlparse

from zm_auto.config import load_config

from .base import BaseSiteAdapter
from .zenmux import ZenmuxAdapter


def _discover() -> dict[str, Any]:
    return {cls.name: cls for cls in BaseSiteAdapter.__subclasses__()}


def get_site_adapter(name: str | None = None) -> BaseSiteAdapter:
    """Return a site adapter instance by name.

    If name is None, use the current configured site_url host as adapter name.
    """
    adapters = _discover()
    if name is None:
        host = urlparse(load_config().site_url).netloc
        name = host.split(".")[0] if host else "zenmux"
    adapter_cls = adapters.get(name)
    if adapter_cls is None:
        raise ValueError(f"未知 site adapter: {name}")
    return cast(BaseSiteAdapter, adapter_cls())


def get_adapter_for_url(url: str) -> BaseSiteAdapter:
    """Return the best matching adapter for a given URL."""
    host = urlparse(url).netloc
    adapters = _discover()
    for name, cls in adapters.items():
        if name and name in host:
            return cast(BaseSiteAdapter, cls())
    # Default fallback
    return get_site_adapter("zenmux")


__all__ = ["BaseSiteAdapter", "ZenmuxAdapter", "get_site_adapter", "get_adapter_for_url"]
