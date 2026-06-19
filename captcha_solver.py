"""⚠️ DISCLAIMER: This project is for educational and research purposes only.
Users are solely responsible for complying with all applicable ToS and laws.
本项目仅供学习研究，使用者需自行承担所有后果。
"""

from __future__ import annotations

import atexit
import os
import tempfile
import time
from typing import Any

import requests

# Target captchas (from protocol analysis + browser debug)
TURNSTILE_SITE_KEY = "0x4AAAAAAB3vWB8HhhtIcASj"
RECAPTCHA_SITE_KEY = "6LdN_REsAAAAAKSlH2k4VNXoCT-Fi1bv_Ufaf86t"


class CaptchaSolver:
    """Multi-provider captcha solver.

    Providers:
      - 2captcha / anticaptcha: paid API, fully automated
      - browser: local Playwright, free for reCAPTCHA, fails for Turnstile
      - cdp: Chrome DevTools Protocol, human-in-the-loop, free
    """

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

        # Browser state (lazy)
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._cdp_solver: Any = None
        self._cdp_recaptcha_solver: Any = None

        if self.provider not in ("browser", "cdp") and not self.api_key:
            raise RuntimeError(
                "CaptchaSolver 需要 api_key。"
                " 免费方案请设置 provider=\"browser\" 或 provider=\"cdp\""
            )

    # ------------------------------------------------------------------ #
    # Browser lifecycle
    # ------------------------------------------------------------------ #
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
            self._browser = self._playwright.chromium.launch(**launch_args)
            self._context = self._browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            )

        atexit.register(self.close)

    def _new_page(self) -> Any:
        self._ensure_browser()
        page = self._context.new_page()
        if self.browser_cfg.get("stealth", True):
            try:
                from playwright_stealth import Stealth
                Stealth().apply_stealth_sync(page)
            except ImportError:
                pass
        return page

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

    @staticmethod
    def _remaining_ms(deadline: float, floor: int = 5000) -> int:
        return max(int((deadline - time.time()) * 1000), floor)

    # ------------------------------------------------------------------ #
    # Turnstile
    # ------------------------------------------------------------------ #
    def solve_turnstile(self, page_url: str = "https://example.com/login", timeout: int = 120) -> str:
        """Solve Cloudflare Turnstile and return the token."""
        if self.provider == "2captcha":
            return self._solve_2captcha_turnstile(page_url, timeout)
        if self.provider == "browser":
            return self._solve_turnstile_browser(page_url, timeout)
        if self.provider == "cdp":
            return self._solve_turnstile_cdp(page_url, timeout)
        raise RuntimeError(f"Turnstile 暂不支持 provider: {self.provider}")

    def _solve_2captcha_turnstile(self, page_url: str, timeout: int) -> str:
        r = requests.post(
            "https://2captcha.com/in.php",
            data={
                "key": self.api_key,
                "method": "turnstile",
                "sitekey": TURNSTILE_SITE_KEY,
                "pageurl": page_url,
                "json": 1,
            },
            timeout=30,
        )
        data = r.json()
        if data.get("status") != 1:
            raise RuntimeError(f"2captcha Turnstile 提交失败: {data}")
        task_id = data["request"]
        return self._poll_2captcha(task_id, timeout)

    def _solve_turnstile_browser(self, page_url: str, timeout: int) -> str:
        deadline = time.time() + timeout
        page = self._new_page()
        try:
            page.goto(page_url, wait_until="domcontentloaded", timeout=self._remaining_ms(deadline))
            time.sleep(3)
            self._click_email_button(page)
            time.sleep(2)
            page.wait_for_selector(
                '[name="cf-turnstile-response"]',
                timeout=self._remaining_ms(deadline, 10000),
            )
            while time.time() < deadline:
                token = page.evaluate(
                    "() => {"
                    "  const el = document.querySelector('[name=\"cf-turnstile-response\"]');"
                    "  return el ? el.value : '';"
                    "}"
                )
                if token and len(token) > 10:
                    return str(token)
                time.sleep(1.5)
            raise RuntimeError(
                f"Turnstile 浏览器超时 ({timeout}s)。"
                " 尝试 provider=\"cdp\" 人工介入方案"
            )
        finally:
            page.close()

    def _solve_turnstile_cdp(self, page_url: str, timeout: int) -> str:
        """CDP human-in-the-loop: connects to user's Chrome, navigates, clicks
        email button, then waits for human to solve Turnstile manually."""
        from cdp_solver import CDPTurnstileSolver

        if self._cdp_solver is None:
            cdp_url = self.browser_cfg.get("cdp_url", "http://127.0.0.1:9222")
            self._cdp_solver = CDPTurnstileSolver(cdp_url)
        return self._cdp_solver.solve(page_url, timeout)

    @staticmethod
    def _click_email_button(page: Any) -> None:
        """Click the email login button, handling multiple languages."""
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

    # ------------------------------------------------------------------ #
    # reCAPTCHA v2
    # ------------------------------------------------------------------ #
    def solve_recaptcha(self, page_url: str = "https://example.com/verify",
                        timeout: int = 180, cookies: list[dict] | None = None) -> str:
        """Solve Google reCAPTCHA v2 and return the token."""
        if self.provider == "2captcha":
            return self._solve_2captcha_recaptcha(page_url, timeout)
        if self.provider == "anticaptcha":
            return self._solve_anticaptcha_recaptcha(page_url, timeout)
        if self.provider == "browser":
            return self._solve_recaptcha_browser(page_url, timeout)
        if self.provider == "cdp":
            return self._solve_recaptcha_cdp(page_url, timeout, cookies)
        raise RuntimeError(f"reCAPTCHA 暂不支持 provider: {self.provider}")

    def _solve_2captcha_recaptcha(self, page_url: str, timeout: int) -> str:
        r = requests.get(
            "https://2captcha.com/in.php",
            params={
                "key": self.api_key,
                "method": "userrecaptcha",
                "googlekey": RECAPTCHA_SITE_KEY,
                "pageurl": page_url,
                "json": 1,
            },
            timeout=30,
        )
        data = r.json()
        if data.get("status") != 1:
            raise RuntimeError(f"2captcha reCAPTCHA 提交失败: {data}")
        task_id = data["request"]
        return self._poll_2captcha(task_id, timeout)

    def _solve_anticaptcha_recaptcha(self, page_url: str, timeout: int) -> str:
        r = requests.post(
            "https://api.anti-captcha.com/createTask",
            json={
                "clientKey": self.api_key,
                "task": {
                    "type": "NoCaptchaTaskProxyless",
                    "websiteURL": page_url,
                    "websiteKey": RECAPTCHA_SITE_KEY,
                },
            },
            timeout=30,
        )
        data = r.json()
        if data.get("errorId"):
            raise RuntimeError(f"anticaptcha 提交失败: {data.get('errorDescription')}")
        task_id = data["taskId"]
        return self._poll_anticaptcha(task_id, timeout)

    def _solve_recaptcha_cdp(self, page_url: str, timeout: int,
                             cookies: list[dict] | None) -> str:
        """CDP human-in-the-loop for reCAPTCHA v2."""
        from cdp_solver import CDPRecaptchaSolver

        if self._cdp_recaptcha_solver is None:
            cdp_url = self.browser_cfg.get("cdp_url", "http://127.0.0.1:9222")
            self._cdp_recaptcha_solver = CDPRecaptchaSolver(cdp_url)
        return self._cdp_recaptcha_solver.solve(
            page_url, timeout=timeout,
            cookies=cookies,
        )

    def _solve_recaptcha_browser(self, page_url: str, timeout: int) -> str:
        deadline = time.time() + timeout
        page = self._new_page()
        try:
            page.goto(page_url, wait_until="domcontentloaded", timeout=self._remaining_ms(deadline))

            recaptcha_frame = page.wait_for_selector(
                "iframe[src*='google.com/recaptcha']",
                timeout=min(self._remaining_ms(deadline), 30000),
            )
            frame = recaptcha_frame.content_frame()
            if not frame:
                raise RuntimeError("无法获取 reCAPTCHA iframe content_frame")

            checkbox = frame.wait_for_selector(
                ".recaptcha-checkbox-border", timeout=self._remaining_ms(deadline, 10000)
            )
            checkbox.click()
            time.sleep(2)

            challenge_frame_el = frame.query_selector("iframe[src*='bframe']")
            if challenge_frame_el:
                challenge_frame = challenge_frame_el.content_frame()
                if not challenge_frame:
                    raise RuntimeError("无法获取 reCAPTCHA challenge iframe")
                self._solve_recaptcha_audio(challenge_frame, deadline)

            while time.time() < deadline:
                token = page.evaluate(
                    "() => {"
                    "  const el = document.querySelector('#g-recaptcha-response');"
                    "  return el ? el.value : '';"
                    "}"
                )
                if token:
                    return str(token)
                time.sleep(1)
            raise RuntimeError(f"reCAPTCHA 浏览器超时 ({timeout}s)")
        finally:
            page.close()

    def _solve_recaptcha_audio(self, frame: Any, deadline: float) -> None:
        audio_btn = frame.wait_for_selector(
            "#recaptcha-audio-button", timeout=self._remaining_ms(deadline, 10000)
        )
        audio_btn.click()
        time.sleep(2)

        audio_link = frame.wait_for_selector(
            ".rc-audiochallenge-tdownload-link", timeout=self._remaining_ms(deadline, 10000)
        )
        audio_url = audio_link.get_attribute("href")
        if not audio_url:
            raise RuntimeError("无法获取 reCAPTCHA 音频下载链接")

        cookies = self._context.cookies()
        cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        resp = requests.get(
            audio_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                "Referer": frame.url,
                "Cookie": cookie_header,
            },
            timeout=self._remaining_ms(deadline, 10000) / 1000.0,
        )
        resp.raise_for_status()
        audio_bytes = resp.content

        text = self._recognize_audio(audio_bytes)

        response_input = frame.wait_for_selector(
            "#audio-response", timeout=self._remaining_ms(deadline, 5000)
        )
        response_input.fill(text)

        verify_btn = frame.wait_for_selector(
            "#recaptcha-verify-button", timeout=self._remaining_ms(deadline, 5000)
        )
        verify_btn.click()
        time.sleep(2)

    def _recognize_audio(self, audio_bytes: bytes) -> str:
        try:
            import speech_recognition as sr
        except ImportError:
            raise RuntimeError(
                "reCAPTCHA 音频识别需要 SpeechRecognition 库: pip install SpeechRecognition pydub"
            )

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(tmp_path) as source:
                audio = recognizer.record(source)
            return recognizer.recognize_google(audio)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    # ------------------------------------------------------------------ #
    # Polling
    # ------------------------------------------------------------------ #
    def _poll_2captcha(self, task_id: str, timeout: int) -> str:
        deadline = time.time() + timeout
        time.sleep(5)
        while time.time() < deadline:
            r = requests.get(
                "https://2captcha.com/res.php",
                params={"key": self.api_key, "action": "get", "id": task_id, "json": 1},
                timeout=30,
            )
            data = r.json()
            if data.get("status") == 1:
                return str(data["request"])
            if data.get("request") != "CAPCHA_NOT_READY":
                raise RuntimeError(f"2captcha 轮询失败: {data}")
            time.sleep(5)
        raise RuntimeError(f"2captcha 超时 ({timeout}s)")

    def _poll_anticaptcha(self, task_id: str, timeout: int) -> str:
        deadline = time.time() + timeout
        time.sleep(5)
        while time.time() < deadline:
            r = requests.post(
                "https://api.anti-captcha.com/getTaskResult",
                json={"clientKey": self.api_key, "taskId": task_id},
                timeout=30,
            )
            data = r.json()
            if data.get("errorId"):
                raise RuntimeError(f"anticaptcha 轮询失败: {data.get('errorDescription')}")
            if data.get("status") == "ready":
                return str(data["solution"]["gRecaptchaResponse"])
            time.sleep(5)
        raise RuntimeError(f"anticaptcha 超时 ({timeout}s)")
