"""Tests for captcha_solver.py (no network/browser calls)."""

import time
from unittest.mock import patch

import pytest

from zm_auto.captcha import CaptchaSolver
from zm_auto.constants import TURNSTILE_SITE_KEY, RECAPTCHA_SITE_KEY


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
class TestConstants:
    def test_turnstile_site_key_is_nonempty(self):
        assert TURNSTILE_SITE_KEY
        assert isinstance(TURNSTILE_SITE_KEY, str)
        assert len(TURNSTILE_SITE_KEY) > 0

    def test_recaptcha_site_key_is_nonempty(self):
        assert RECAPTCHA_SITE_KEY
        assert isinstance(RECAPTCHA_SITE_KEY, str)
        assert len(RECAPTCHA_SITE_KEY) > 0


# --------------------------------------------------------------------------- #
# Constructor
# --------------------------------------------------------------------------- #
class TestCaptchaSolverInit:
    def test_2captcha_with_api_key(self):
        solver = CaptchaSolver(api_key="test-key", provider="2captcha")
        assert solver.api_key == "test-key"
        assert solver.provider == "2captcha"

    def test_anticaptcha_with_api_key(self):
        solver = CaptchaSolver(api_key="test-key", provider="anticaptcha")
        assert solver.api_key == "test-key"
        assert solver.provider == "anticaptcha"

    def test_browser_without_api_key(self):
        solver = CaptchaSolver(provider="browser")
        assert solver.provider == "browser"
        assert solver.api_key == ""

    def test_cdp_without_api_key(self):
        solver = CaptchaSolver(provider="cdp")
        assert solver.provider == "cdp"
        assert solver.api_key == ""

    def test_2captcha_without_api_key_raises(self):
        with pytest.raises(RuntimeError, match="api_key"):
            CaptchaSolver(provider="2captcha", api_key="")

    def test_anticaptcha_without_api_key_raises(self):
        with pytest.raises(RuntimeError, match="api_key"):
            CaptchaSolver(provider="anticaptcha", api_key="")

    def test_provider_case_insensitive(self):
        solver = CaptchaSolver(api_key="k", provider="2Captcha")
        assert solver.provider == "2captcha"

    def test_provider_from_env(self):
        """When provider arg is empty, fall back to CAPTCHA_PROVIDER env var."""
        solver = CaptchaSolver(provider="", api_key="k")
        # With empty provider and no env var set, defaults to "2captcha"
        assert solver.provider == "2captcha"

    def test_provider_from_env_var(self, monkeypatch):
        """When provider arg is empty, use CAPTCHA_PROVIDER env var."""
        monkeypatch.setenv("CAPTCHA_PROVIDER", "browser")
        solver = CaptchaSolver(provider="")
        assert solver.provider == "browser"

    def test_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("CAPTCHA_API_KEY", "env-key")
        solver = CaptchaSolver(provider="2captcha")
        assert solver.api_key == "env-key"

    def test_explicit_api_key_overrides_env(self, monkeypatch):
        monkeypatch.setenv("CAPTCHA_API_KEY", "env-key")
        solver = CaptchaSolver(api_key="explicit-key", provider="2captcha")
        assert solver.api_key == "explicit-key"

    def test_browser_cfg_defaults(self):
        solver = CaptchaSolver(provider="browser")
        assert solver.browser_cfg == {}

    def test_browser_cfg_passed(self):
        cfg = {"headless": False, "stealth": True}
        solver = CaptchaSolver(provider="browser", browser_cfg=cfg)
        assert solver.browser_cfg == cfg

    def test_proxy_passed(self):
        solver = CaptchaSolver(provider="browser", proxy="http://127.0.0.1:7890")
        assert solver.proxy == "http://127.0.0.1:7890"


# --------------------------------------------------------------------------- #
# _remaining_ms
# --------------------------------------------------------------------------- #
class TestRemainingMs:
    def test_returns_minimum_floor(self):
        """When deadline is far in the past, return the floor value."""
        deadline = time.time() - 100
        result = CaptchaSolver._remaining_ms(deadline, floor=5000)
        assert result == 5000

    def test_returns_calculated_value(self):
        """When deadline is far enough in future, return calculated value."""
        now = time.time()
        deadline = now + 10  # 10 seconds from now
        result = CaptchaSolver._remaining_ms(deadline, floor=1000)
        assert 8000 <= result <= 10500  # around 10000ms, with tolerance

    def test_custom_floor(self):
        deadline = time.time() - 100
        result = CaptchaSolver._remaining_ms(deadline, floor=1000)
        assert result == 1000


# --------------------------------------------------------------------------- #
# Provider dispatch (without actual solving)
# --------------------------------------------------------------------------- #
class TestProviderDispatch:
    def test_solve_turnstile_2captcha(self):
        solver = CaptchaSolver(api_key="k", provider="2captcha")
        with patch.object(solver, "_solve_2captcha_turnstile", return_value="token-123") as mock:
            result = solver.solve_turnstile("https://example.com/login")
            assert result == "token-123"
            mock.assert_called_once()

    def test_solve_turnstile_browser(self):
        solver = CaptchaSolver(provider="browser")
        with patch.object(solver, "_solve_turnstile_browser", return_value="token-456") as mock:
            result = solver.solve_turnstile("https://example.com/login")
            assert result == "token-456"
            mock.assert_called_once()

    def test_solve_turnstile_cdp(self):
        solver = CaptchaSolver(provider="cdp")
        with patch.object(solver, "_solve_turnstile_cdp", return_value="token-789") as mock:
            result = solver.solve_turnstile("https://example.com/login")
            assert result == "token-789"
            mock.assert_called_once()
