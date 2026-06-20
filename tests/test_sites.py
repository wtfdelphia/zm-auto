"""Tests for site adapter registry."""
from __future__ import annotations

from zm_auto.sites import ZenmuxAdapter, get_adapter_for_url, get_site_adapter


def test_get_site_adapter_by_name() -> None:
    adapter = get_site_adapter("zenmux")
    assert isinstance(adapter, ZenmuxAdapter)
    assert adapter.name == "zenmux"


def test_get_site_adapter_default() -> None:
    adapter = get_site_adapter()
    assert isinstance(adapter, ZenmuxAdapter)


def test_get_adapter_for_url() -> None:
    adapter = get_adapter_for_url("https://zenmux.ai")
    assert isinstance(adapter, ZenmuxAdapter)


def test_zenmux_paths() -> None:
    adapter = get_site_adapter("zenmux")
    assert adapter.user_info_path() == "/api/user/info"
    assert adapter.api_key_list_path() == "/api/api_key/list"
    assert adapter.api_key_page_path() == "/platform/pay-as-you-go"
    endpoints = adapter.register_endpoints()
    assert "send_code" in endpoints
