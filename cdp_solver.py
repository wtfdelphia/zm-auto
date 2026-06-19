"""⚠️ DISCLAIMER: This project is for educational and research purposes only.
CDP-based captcha solvers: connects to a user-launched Chrome for human-in-the-loop.
Supports Turnstile, reCAPTCHA v2, and full browser login flow.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"


def _load_site_url() -> str:
    """读取 config.json 中的目标站点地址，失败时使用默认地址。"""
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg = json.load(f)
        return str(cfg.get("site_url", "https://zenmux.ai")).rstrip("/")
    except Exception:
        return "https://zenmux.ai"


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
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


def _cdp_connect(cdp_url: str) -> tuple[Any, Any]:
    """Connect to a Chrome via CDP. Returns (playwright, browser)."""
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(cdp_url)
    return pw, browser


def _cdp_new_page(browser: Any, cookies: list[dict] | None = None) -> Any:
    """Create a new page in the CDP browser, optionally injecting cookies."""
    if browser.contexts:
        page = browser.contexts[0].new_page()
    else:
        page = browser.new_page()
    if cookies:
        page.context.add_cookies(cookies)
    return page


# --------------------------------------------------------------------------- #
# CDP Turnstile solver (standalone)
# --------------------------------------------------------------------------- #
class CDPTurnstileSolver:
    """Human-in-the-loop Turnstile solver via CDP. Navigates to login page,
    clicks email button, waits for human to solve Turnstile, returns token."""

    def __init__(self, cdp_url: str = "http://127.0.0.1:9222"):
        self.cdp_url = cdp_url
        self._playwright: Any = None
        self._browser: Any = None
    def close(self) -> None:
        """Close the CDP browser and stop Playwright."""
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
        self._browser = None
        self._playwright = None

    def _connect(self) -> None:
        if self._browser is not None:
            return
        self._playwright, self._browser = _cdp_connect(self.cdp_url)

    def solve(self, page_url: str, timeout: int = 300,
              cookies: list[dict] | None = None) -> str:
        self._connect()
        page = _cdp_new_page(self._browser, cookies)

        page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        _click_email_button(page)
        time.sleep(2)

        print("\n" + "=" * 50)
        print(" 请在 Chrome 窗口中手动完成 Turnstile 验证")
        print(" 完成后脚本会自动检测并继续...")
        print("=" * 50 + "\n")

        deadline = time.time() + timeout
        while time.time() < deadline:
            token = page.evaluate(
                "() => {"
                "  const el = document.querySelector('[name=\"cf-turnstile-response\"]');"
                "  return el ? el.value : '';"
                "}"
            )
            if token and len(token) > 10:
                print(f" Turnstile 通过! token={token[:30]}...")
                return str(token)
            time.sleep(1)

        raise RuntimeError(f"等待 Turnstile 超时 ({timeout}s)")


# --------------------------------------------------------------------------- #
# CDP reCAPTCHA solver (standalone)
# --------------------------------------------------------------------------- #
class CDPRecaptchaSolver:
    """Human-in-the-loop reCAPTCHA v2 solver via CDP."""

    def __init__(self, cdp_url: str = "http://127.0.0.1:9222"):
        self.cdp_url = cdp_url
        self._playwright: Any = None
        self._browser: Any = None
    def close(self) -> None:
        """Close the CDP browser and stop Playwright."""
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
        self._browser = None
        self._playwright = None

    def _connect(self) -> None:
        if self._browser is not None:
            return
        self._playwright, self._browser = _cdp_connect(self.cdp_url)

    def solve(self, page_url: str, timeout: int = 300,
              cookies: list[dict] | None = None) -> str:
        self._connect()
        page = _cdp_new_page(self._browser, cookies)

        page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        print("\n" + "=" * 50)
        print(" 请在 Chrome 窗口中手动完成 reCAPTCHA 验证")
        print(" （点击复选框 → 如有图片挑战请手动完成）")
        print(" 完成后脚本会自动检测并继续...")
        print("=" * 50 + "\n")

        deadline = time.time() + timeout
        while time.time() < deadline:
            token = page.evaluate(
                "() => {"
                "  const el = document.querySelector('#g-recaptcha-response');"
                "  return el ? el.value : '';"
                "}"
            )
            if token and len(token) > 10:
                print(f" reCAPTCHA 通过! token={token[:30]}...")
                return str(token)
            time.sleep(1)

        raise RuntimeError(f"等待 reCAPTCHA 超时 ({timeout}s)")


# --------------------------------------------------------------------------- #
# CDP Login solver (full flow: Turnstile → email → code → verify)
# --------------------------------------------------------------------------- #
class CDPLoginSolver:
    """Full browser login flow via CDP.

    1. Navigate to /login, click Email button
    2. Human solves Turnstile
    3. Auto-fill email, click Send
    4. Wait for verification code input to appear
    5. Call get_code() callback to fetch code from email
    6. Auto-fill code, click Verify
    7. Wait for login redirect, extract session cookies

    Usage:
      solver = CDPLoginSolver()
      cookies = solver.login("https://example.com/login", email, get_code_fn)
    """

    def __init__(self, cdp_url: str = "http://127.0.0.1:9222", site_url: str = "", invite_code: str = ""):
        self.cdp_url = cdp_url
        self.site_url = site_url or _load_site_url()
        self.invite_code = invite_code
        self._playwright: Any = None
        self._browser: Any = None
    def close(self) -> None:
        """Close the CDP browser and stop Playwright."""
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
        self._browser = None
        self._playwright = None

    def _connect(self) -> None:
        if self._browser is not None:
            return
        self._playwright, self._browser = _cdp_connect(self.cdp_url)


    def _fill_invite_code(self, page: Any) -> None:
        """如果配置了邀请码，尝试在登录表单中自动填写。"""
        if not self.invite_code:
            return
        try:
            filled = page.evaluate(
                """
                (code) => {
                    const selectors = [
                        'input[name=\"invite_code\"]', 'input[name=\"inviteCode\"]', 'input[name=\"invite\"]', 'input[name=\"referral\"]', 'input[name=\"referral_code\"]', 'input[name=\"referralCode\"]',
                        'input[placeholder*=\"邀请\" i]', 'input[placeholder*=\"invite\" i]', 'input[placeholder*=\"推荐\" i]',
                        'input[aria-label*=\"邀请\" i]', 'input[aria-label*=\"invite\" i]', 'input[aria-label*=\"推荐\" i]'
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.offsetParent !== null) {
                            el.focus();
                            el.value = code;
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            return true;
                        }
                    }
                    return false;
                }
                """, self.invite_code
            )
            if filled:
                print(f"  已自动填写邀请码: {self.invite_code}")
        except Exception as e:
            print(f"  邀请码填写失败: {e}")

    def login(
        self,
        page_url: str,
        email: str,
        get_code: Callable[[], str | None],
        timeout: int = 300,
    ) -> list[dict]:
        """Run full login flow. get_code is called repeatedly until it returns
        a non-empty string (the 6-digit verification code). Returns browser
        cookies as a list of dicts for injection into the HTTP session."""
        self._connect()
        page = _cdp_new_page(self._browser)

        deadline = time.time() + timeout

        # ---- 1. Navigate & click Email ----
        page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        _click_email_button(page)
        time.sleep(2)

        # If invite code configured, try to fill it after the login form appears
        self._fill_invite_code(page)

        # ---- 2. Human solves Turnstile ----
        print("\n" + "=" * 50)
        print(" 请在 Chrome 窗口中手动完成 Turnstile 验证")
        print(" 完成后脚本会自动继续...")
        print("=" * 50 + "\n")

        while time.time() < deadline:
            token = page.evaluate(
                "() => {"
                "  const el = document.querySelector('[name=\"cf-turnstile-response\"]');"
                "  return el ? el.value : '';"
                "}"
            )
            if token and len(token) > 10:
                print(" Turnstile 通过!")
                break
            time.sleep(1)
        else:
            raise RuntimeError(f"等待 Turnstile 超时 ({timeout}s)")

        # ---- 3. Fill email & click Send ----
        time.sleep(1)
        print(f" 填写邮箱: {email}")
        self._fill_input(page, email, [
            'input[type="email"]',
            'input[name="email"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="邮箱" i]',
            'input[placeholder*="Email" i]',
        ])
        time.sleep(0.5)

        print(" 点击发送验证码...")

        # Intercept the API response to verify email was sent
        send_ok = False

        def _check_response(response):
            nonlocal send_ok
            if "/login/email/code/send" in response.url and response.status == 200:
                try:
                    body = response.json()
                    if body.get("success"):
                        send_ok = True
                        print(f"   API确认: 验证码已发送")
                except Exception:
                    pass

        page.on("response", _check_response)
        self._click_button(page, [
            'button:has-text("发送")',
            'button:has-text("Send")',
            'button:has-text("获取验证码")',
            'button:has-text("Get Code")',
            '[class*="send"]',
            '[class*="Send"]',
        ])

        time.sleep(2)
        if not send_ok:
            print("   ⚠ 未检测到发送成功的API响应，可能需要检查页面状态")

        # ---- 4. Poll email + wait for input field (parallel) ----
        import threading
        code_result = [None]
        code_error = [None]

        def _poll_email():
            try:
                code_result[0] = get_code()
            except Exception as e:
                code_error[0] = e

        print(" 启动邮箱轮询线程...")
        code_thread = threading.Thread(target=_poll_email, daemon=True)
        code_thread.start()

        # Wait for code input field to appear (max 30s, then continue anyway)
        print(" 等待验证码输入框出现...")
        field_deadline = time.time() + 30
        input_ready = False
        while time.time() < field_deadline:
            for sel in [
                'input[placeholder*="验证码" i]',
                'input[placeholder*="code" i]',
                'input[placeholder*="Code" i]',
                'input[type="text"]',
            ]:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        input_ready = True
                        print(f" 输入框已出现 (selector: {sel})")
                        break
                except Exception:
                    pass
            if input_ready:
                break
            time.sleep(1)
        if not input_ready:
            print("  ⚠ 输入框未在30s内出现，继续等待验证码...")

        # Wait for email code (with remaining deadline)
        print(" 等待邮箱验证码...")
        remaining = deadline - time.time()
        code_thread.join(timeout=max(1, remaining))
        code = code_result[0]

        if code_error[0]:
            print(f"  ⚠ 邮箱轮询异常: {code_error[0]}")
        if not code:
            raise RuntimeError(f"未能获取邮箱验证码 (轮询了 {remaining:.0f}s, input_ready={input_ready})")
        print(f" 收到验证码: {code}")

        # ---- 6. Fill code & click Verify ----
        print(" 填写验证码...")
        self._fill_input(page, code, [
            'input[placeholder*="验证码" i]',
            'input[placeholder*="code" i]',
            'input[placeholder*="Code" i]',
            'input[type="text"]',
        ])
        time.sleep(0.5)

        print(" 点击验证...")
        self._click_button(page, [
            'button:has-text("验证")',
            'button:has-text("Verify")',
            'button:has-text("登录")',
            'button:has-text("Login")',
            'button:has-text("确认")',
            'button:has-text("Submit")',
            '[type="submit"]',
        ])

        # ---- 7. Wait for login redirect ----
        print(" 等待登录完成...")
        try:
            page.wait_for_url("**/platform/**", timeout=15000)
        except Exception:
            time.sleep(2)
        current_url = page.url
        print(f" 当前页面: {current_url}")
        if "waitlist" in current_url:
            print("  ⚠ 账号被 waitlist，可能无法创建 API Key")
        print(" 登录完成!\n")

        # ---- 8. Extract CSRF token + cookies ----
        cookies = page.context.cookies()
        print(f"  获取到 {len(cookies)} 个 cookie:")
        for c in cookies:
            print(f"    {c['name']}={c['value'][:30]}{'...' if len(c.get('value',''))>30 else ''}")
        
        # Extract CSRF token from page meta or cookie
        csrf_token = ""
        try:
            csrf_token = page.evaluate("""
                () => {
                    const meta = document.querySelector('meta[name="csrf-token"]');
                    if (meta) return meta.getAttribute("content") || "";
                    const meta2 = document.querySelector('meta[name="_csrf"]');
                    if (meta2) return meta2.getAttribute("content") || "";
                    return "";
                }
            """)
        except Exception:
            pass
        if not csrf_token:
            # Try from cookies
            for c in cookies:
                if c["name"].lower() in ("csrf_token", "_csrf", "xsrf-token", "csrf-token"):
                    csrf_token = c["value"]
                    break
        if csrf_token:
            print(f"  CSRF token: {csrf_token[:30]}...")
        else:
            print("  ⚠ 未找到 CSRF token")
        
        return {"cookies": cookies, "csrf_token": csrf_token}


    def logout(self) -> None:
        """Log out from zenmux in the browser, clearing the session."""
        if self._browser is None:
            return
        try:
            page = _cdp_new_page(self._browser)
            # Navigate to logout
            page.goto(f"{self.site_url}/logout", wait_until="domcontentloaded", timeout=10000)
            time.sleep(1)
            print("  浏览器已退出登录")
            page.close()
        except Exception as e:
            print(f"  退出登录失败: {e}")
            # Fallback: clear cookies for zenmux domain
            try:
                context = self._browser.contexts[0] if self._browser.contexts else None
                if context:
                    context.clear_cookies()
                    print("  已清除浏览器 cookies")
            except Exception:
                pass

    # -- helpers --
    @staticmethod
    def _fill_input(page: Any, text: str, selectors: list[str]) -> None:
        # Strategy 1: try explicit selectors
        for sel in selectors:
            try:
                el = page.wait_for_selector(sel, timeout=3000)
                if el.is_visible():
                    el.fill(text)
                    print(f"  输入框已填充 (selector: {sel})")
                    return
            except Exception:
                continue
        # Strategy 2: find any visible text/number input that's not email
        print("  策略1失败，尝试查找任意可见输入框...")
        try:
            inputs = page.query_selector_all("input")
            for inp in inputs:
                try:
                    if not inp.is_visible():
                        continue
                    inp_type = (inp.get_attribute("type") or "").lower()
                    inp_placeholder = (inp.get_attribute("placeholder") or "").lower()
                    inp_name = (inp.get_attribute("name") or "").lower()
                    if inp_type == "email" or "email" in inp_placeholder or "邮箱" in inp_placeholder:
                        continue
                    if inp_type in ("", "text", "number", "tel"):
                        inp.fill(text)
                        print(f"  输入框已填充 (type={inp_type}, placeholder={inp_placeholder[:30]})")
                        return
                except Exception:
                    continue
        except Exception:
            pass
        # Strategy 3: JavaScript fallback
        print("  策略2失败，尝试 JS 查找并填充...")
        try:
            result = page.evaluate("""
                (text) => {
                    const inputs = document.querySelectorAll(
                        "input:not([type=email]):not([type=hidden]):not([type=submit]):not([type=checkbox])"
                    );
                    for (const inp of inputs) {
                        if (inp.offsetParent !== null) {
                            inp.focus();
                            inp.value = text;
                            inp.dispatchEvent(new Event("input", { bubbles: true }));
                            inp.dispatchEvent(new Event("change", { bubbles: true }));
                            return { ok: true, type: inp.type, placeholder: inp.placeholder };
                        }
                    }
                    return { ok: false };
                }
            """, text)
            if result.get("ok"):
                print(f"  JS填充成功 (type={result.get('type')}, placeholder={result.get('placeholder', '')[:30]})")
                return
        except Exception as e:
            print(f"  JS策略异常: {e}")
        raise RuntimeError(f"找不到输入框, tried: {selectors}")


    @staticmethod
    def _click_button(page: Any, selectors: list[str]) -> None:
        for sel in selectors:
            try:
                el = page.wait_for_selector(sel, timeout=3000)
                if el.is_visible():
                    el.click()
                    return
            except Exception:
                continue
        raise RuntimeError(f"找不到按钮, tried: {selectors}")

    @staticmethod
    def _wait_for_selector_any(page: Any, selectors: list[str], deadline: float) -> None:
        while time.time() < deadline:
            for sel in selectors:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        return
                except Exception:
                    pass
            time.sleep(1)
        raise RuntimeError(f"等待元素超时, tried: {selectors}")


# --------------------------------------------------------------------------- #
# Standalone test
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "turnstile"
    url = sys.argv[2] if len(sys.argv) > 2 else ""
    hint = (
        "\n请确保 Chrome 已启动:\n"
        '  open -a "Google Chrome" --args \\\n'
        '    --remote-debugging-port=9222 \\\n'
        '    --proxy-server="http://127.0.0.1:7890" \\\n'
        '    --user-data-dir=/tmp/chrome-cdp\n'
    )

    if mode == "recaptcha":
        url = url or f"{_load_site_url()}/verify?method=unknown"
        solver = CDPRecaptchaSolver()
        try:
            token = solver.solve(url)
            print(f"\nToken: {token}")
        except Exception as e:
            print(f"\n失败: {e}{hint}")

    elif mode == "login":
        url = url or f"{_load_site_url()}/login"
        email = sys.argv[3] if len(sys.argv) > 3 else ""
        if not email:
            print("用法: python cdp_solver.py login <url> <email>")
            sys.exit(1)

        def dummy_get_code() -> str | None:
            return input("请输入邮箱验证码: ").strip() or None

        solver = CDPLoginSolver()
        try:
            result = solver.login(url, email, dummy_get_code)
            cookies = result.get("cookies", [])
            print(f"\nCookies: {len(cookies)} 个")
            for c in cookies:
                print(f"  {c['name']}={c['value'][:20]}...")
        except Exception as e:
            print(f"\n失败: {e}{hint}")

    else:
        url = url or f"{_load_site_url()}/login"
        solver = CDPTurnstileSolver()
        try:
            token = solver.solve(url)
            print(f"\nToken: {token}")
        except Exception as e:
            print(f"\n失败: {e}{hint}")
