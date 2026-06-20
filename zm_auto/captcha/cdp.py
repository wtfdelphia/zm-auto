"""CDP human-in-the-loop captcha solvers."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import time
from typing import Any

from zm_auto.cdp.session import CDPSession
from zm_auto.constants import CDP_URL


class CDPTurnstileSolver:
    """Human-in-the-loop Turnstile solver via CDP."""

    def __init__(self, cdp_url: str = CDP_URL):
        self.cdp_url = cdp_url

    def solve(self, page_url: str, timeout: int = 300, cookies: list[dict] | None = None) -> str:
        with CDPSession(self.cdp_url, cookies) as session:
            page = session.page
            page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            _click_email_button(page)
            time.sleep(2)

            logger.info("\n" + "=" * 50)
            logger.info(" 请在 Chrome 窗口中手动完成 Turnstile 验证")
            logger.info(" 完成后脚本会自动检测并继续...")
            logger.info("=" * 50 + "\n")

            deadline = time.time() + timeout
            while time.time() < deadline:
                token = page.evaluate("""() => {
                    const el = document.querySelector('[name=\"cf-turnstile-response"]');
                    return el ? el.value : '';
                }""")
                if token and len(token) > 10:
                    logger.info(f" Turnstile 通过! token={token[:30]}...")
                    return str(token)
                time.sleep(1)

        raise RuntimeError(f"等待 Turnstile 超时 ({timeout}s)")

    def close(self) -> None:
        """兼容 CaptchaSolver 生命周期管理，实际由 CDPSession 上下文释放。"""
        pass


class CDPRecaptchaSolver:
    """Human-in-the-loop reCAPTCHA v2 solver via CDP."""

    def __init__(self, cdp_url: str = CDP_URL):
        self.cdp_url = cdp_url

    def solve(self, page_url: str, timeout: int = 300, cookies: list[dict] | None = None) -> str:
        with CDPSession(self.cdp_url, cookies) as session:
            page = session.page
            page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

            logger.info("\n" + "=" * 50)
            logger.info(" 请在 Chrome 窗口中手动完成 reCAPTCHA 验证")
            logger.info(" （点击复选框 → 如有图片挑战请手动完成）")
            logger.info(" 完成后脚本会自动检测并继续...")
            logger.info("=" * 50 + "\n")

            deadline = time.time() + timeout
            while time.time() < deadline:
                token = page.evaluate("""() => {
                    const el = document.querySelector('#g-recaptcha-response');
                    return el ? el.value : '';
                }""")
                if token and len(token) > 10:
                    logger.info(f" reCAPTCHA 通过! token={token[:30]}...")
                    return str(token)
                time.sleep(1)

        raise RuntimeError(f"等待 reCAPTCHA 超时 ({timeout}s)")

    def close(self) -> None:
        """兼容 CaptchaSolver 生命周期管理，实际由 CDPSession 上下文释放。"""
        pass


def _click_email_button(page: Any) -> None:
    try:
        page.click("[class*='emailMethod']", timeout=5000)
        return
    except Exception:
        pass
    buttons = page.query_selector_all("button")
    for b in buttons:
        txt = (b.inner_text() or "").strip()
        if any(kw in txt for kw in [
            "Email", "email", "邮箱", "郵件", "メール", "이메일", "e-mail", "E-mail",
        ]):
            b.click()
            return
    if len(buttons) >= 4:
        buttons[3].click()
