"""Tests for CDP stealth script injection."""
from __future__ import annotations

from unittest.mock import MagicMock

from zm_auto.cdp.session import CDPSession
from zm_auto.cdp.stealth import STEALTH_SCRIPT


def test_stealth_script_contains_detection_hiding_code() -> None:
    assert "webdriver" in STEALTH_SCRIPT
    assert "plugins" in STEALTH_SCRIPT
    assert "languages" in STEALTH_SCRIPT
    assert "window.chrome" in STEALTH_SCRIPT
    assert "permissions" in STEALTH_SCRIPT


def test_add_stealth_scripts_injects_once() -> None:
    session = CDPSession()
    page = MagicMock()
    session.add_stealth_scripts(page)
    page.add_init_script.assert_called_once()
    script = page.add_init_script.call_args[0][0]
    assert "webdriver" in script


def test_add_stealth_scripts_is_idempotent() -> None:
    session = CDPSession()
    page = MagicMock()
    session.add_stealth_scripts(page)
    session.add_stealth_scripts(page)
    assert page.add_init_script.call_count == 2


def test_add_stealth_scripts_handles_none_page() -> None:
    session = CDPSession()
    session.add_stealth_scripts(None)  # type: ignore[arg-type]
