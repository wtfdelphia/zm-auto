"""Captcha solver entry point."""
from __future__ import annotations

import atexit
import os
from typing import Any

from zm_auto.captcha.browser import solve_recaptcha_browser, solve_turnstile_browser
from zm_auto.captcha.cdp import CDPRecaptchaSolver, CDPTurnstileSolver
from zm_auto.captcha.paid_api import (
    solve_2captcha_recaptcha,
    solve_2captcha_turnstile,
    solve_anticaptcha_recaptcha,
)
from zm_auto.constants import CDP_URL


class CaptchaSolver:
    """Multi-provider captcha solver."""

    def __init__(
        self,
        api_key: str = "",
        provider: str = "2captcha",
        proxy: str = "",
        browser_cfg: dict[str, Any] | None = None,
    ):
        self.api_key = api_key or os.environ.get("CAPTCHA_API_KEY", "")
        self.provider = (provider or os.environ.get("CAPTCHA_PROVIDER", "2captcha")).lower()
        self.proxy = proxy
        self.browser_cfg = browser_cfg or {}

        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._cdp_solver: CDPTurnstileSolver | None = None
        self._cdp_recaptcha_solver: CDPRecaptchaSolver | None = None

        if self.provider not in ("browser", "cdp") and not self.api_key:
            raise RuntimeError(
                "CaptchaSolver 需要 api_key。免费方案请设置 provider=\"browser\" 或 provider=\"cdp\""
            )

    @staticmethod
    def _remaining_ms(deadline: float, floor: int = 5000) -> int:
        import time
        return max(int((deadline - time.time()) * 1000), floor)

    def _ensure_browser(self) -> None:
        if self._browser is not None or self._context is not None:
            return
        try:
            from patchright.sync_api import sync_playwright
        except ImportError:
            from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        headless = self.browser_cfg.get("headless", True)
        channel = self.browser_cfg.get("channel", "")
        user_data_dir = self.browser_cfg.get("user_data_dir", "")

        launch_args: dict[str, Any] = {"headless": headless}
        if channel:
            launch_args["channel"] = channel
        if self.proxy:
            launch_args["proxy"] = {"server": self.proxy}

        if user_data_dir:
            self._context = self._playwright.chromium.launch_persistent_context(
                user_data_dir, **launch_args
            )
            self._browser = self._context.browser
        else:
            from zm_auto.constants import USER_AGENT
            self._browser = self._playwright.chromium.launch(**launch_args)
            self._context = self._browser.new_context(user_agent=USER_AGENT)

        atexit.register(self.close)

    def close(self) -> None:
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._context = None
        self._browser = None
        self._playwright = None
        try:
            if self._cdp_solver:
                self._cdp_solver.close()
        except Exception:
            pass
        try:
            if self._cdp_recaptcha_solver:
                self._cdp_recaptcha_solver.close()
        except Exception:
            pass

    def _solve_2captcha_turnstile(self, page_url: str, timeout: int) -> str:
        return solve_2captcha_turnstile(self.api_key, page_url, timeout)

    def _solve_turnstile_browser(self, page_url: str, timeout: int) -> str:
        self._ensure_browser()
        return solve_turnstile_browser(self._context, page_url, timeout)

    def _solve_turnstile_cdp(self, page_url: str, timeout: int) -> str:
        cdp_url = self.browser_cfg.get("cdp_url", CDP_URL)
        if self._cdp_solver is None:
            self._cdp_solver = CDPTurnstileSolver(cdp_url)
        return self._cdp_solver.solve(page_url, timeout)

    def solve_turnstile(self, page_url: str = "https://example.com/login", timeout: int = 120) -> str:
        if self.provider == "2captcha":
            return self._solve_2captcha_turnstile(page_url, timeout)
        if self.provider == "browser":
            return self._solve_turnstile_browser(page_url, timeout)
        if self.provider == "cdp":
            return self._solve_turnstile_cdp(page_url, timeout)
        raise RuntimeError(f"Turnstile 暂不支持 provider: {self.provider}")

    def solve_recaptcha(
        self,
        page_url: str = "https://example.com/verify",
        timeout: int = 180,
        cookies: list[dict] | None = None,
    ) -> str:
        if self.provider == "2captcha":
            return solve_2captcha_recaptcha(self.api_key, page_url, timeout)
        if self.provider == "anticaptcha":
            return solve_anticaptcha_recaptcha(self.api_key, page_url, timeout)
        if self.provider == "browser":
            self._ensure_browser()
            return solve_recaptcha_browser(self._context, page_url, timeout)
        if self.provider == "cdp":
            cdp_url = self.browser_cfg.get("cdp_url", CDP_URL)
            if self._cdp_recaptcha_solver is None:
                self._cdp_recaptcha_solver = CDPRecaptchaSolver(cdp_url)
            return self._cdp_recaptcha_solver.solve(page_url, timeout=timeout, cookies=cookies)
        raise RuntimeError(f"reCAPTCHA 暂不支持 provider: {self.provider}")
