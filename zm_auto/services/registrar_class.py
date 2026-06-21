"""Registrar class implementation."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import json
import random
from datetime import datetime, timezone
import string
from typing import Any
from urllib.parse import urlparse


from zm_auto.captcha import CaptchaSolver
from zm_auto.constants import USER_AGENT
from zm_auto.http import make_session
from zm_auto.importers import Sub2APIImporter
from zm_auto.providers import create_mailbox, wait_for_code
from zm_auto.services.registrar_core import (
    API_BASE,
    TARGET_BASE,
    config,
    step,
    _api_headers,
)

class Registrar:
    """Handles one full registration attempt — pure HTTP."""

    def __init__(self, proxy: str = "", captcha_cfg: dict | None = None):
        self.proxy = proxy
        self.captcha_cfg = captcha_cfg or {}
        self.session = make_session(proxy)
        self.ctoken = ""
        self.csrf_token = ""
        self._cdp_solver: Any = None
        self.solver: CaptchaSolver | None = None
        self.mailbox: dict[str, Any] = {}

    def close(self) -> None:
        """关闭验证码 solver 和 CDP 浏览器（在 worker 线程执行）。

        HTTP session 不在这里关闭，以便主线程在文件写入后继续使用它调用服务端 logout。
        """
        try:
            if self.solver:
                self.solver.close()
        except Exception:
            pass
        try:
            if self._cdp_solver:
                self._cdp_solver.close()
        except Exception:
            pass

    def logout(self) -> None:
        """调用服务端退出登录接口（应在文件写入后执行）。

        为避免在 worker 线程外的线程调用 Playwright page 对象，这里通过本 Registrar
        的 HTTP session 发起 POST，带上与登录相同的 session cookies。
        """
        if not config.get("logout_after", True):
            return
        if not self.ctoken:
            return
        try:
            import urllib.parse as _up
            from zm_auto.constants import USER_AGENT
            logout_url = f"{TARGET_BASE}/api/user/logout?ctoken={_up.quote(self.ctoken)}"
            # 使用最小请求头，匹配浏览器内 fetch 行为；避免 application/json 引起服务端 500
            headers = {
                "User-Agent": USER_AGENT,
                "Referer": f"{TARGET_BASE}/",
                "Accept": "application/json, text/plain, */*",
            }
            resp = self.session.post(logout_url, headers=headers, timeout=10, verify=False)
            if resp.status_code == 200:
                logger.info(f"  服务端退出登录: HTTP {resp.status_code}")
            else:
                body = resp.text[:300]
                logger.info(f"  服务端退出登录: HTTP {resp.status_code}, body={body}")
        except Exception as e:
            logger.info(f"  退出登录失败: {e}")
        finally:
            try:
                self.session.close()
            except Exception:
                pass

    @property
    def captcha(self) -> CaptchaSolver:
        if not self.solver:
            self.solver = CaptchaSolver(proxy=self.proxy, browser_cfg=self.captcha_cfg.get("browser", {}),
                api_key=self.captcha_cfg.get("api_key", ""),
                provider=self.captcha_cfg.get("provider", "2captcha"),
            )
        return self.solver

    # ------------------------------------------------------------------ #
    # HTTP helpers
    # ------------------------------------------------------------------ #
    def _url(self, path: str) -> str:
        url = f"{API_BASE}{path}"
        if self.ctoken:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}ctoken={self.ctoken}"
        return url

    def _post(self, path: str, payload: dict | None = None, referer: str = "", expected: tuple[int, ...] = (200,)) -> dict:
        headers = _api_headers(referer)
        if self.csrf_token:
            headers["x-csrf-token"] = self.csrf_token
            headers["x-xsrf-token"] = self.csrf_token
        resp = self.session.post(
            self._url(path),
            headers=headers,
            json=payload,
            timeout=30,
            verify=False,
        )
        if resp.status_code not in expected:
            raise RuntimeError(f"POST {path} 失败: HTTP {resp.status_code}, body={resp.text[:500]}")
        try:
            return resp.json() if isinstance(resp.json(), dict) else {}
        except Exception:
            return {}

    def _get(self, path: str, referer: str = "", expected: tuple[int, ...] = (200,)) -> dict:
        headers = _api_headers(referer)
        if self.csrf_token:
            headers["x-csrf-token"] = self.csrf_token
            headers["x-xsrf-token"] = self.csrf_token
        resp = self.session.get(
            self._url(path),
            headers=headers,
            timeout=30,
            verify=False,
        )
        if resp.status_code not in expected:
            raise RuntimeError(f"GET {path} 失败: HTTP {resp.status_code}, body={resp.text[:500]}")
        try:
            return resp.json() if isinstance(resp.json(), dict) else {}
        except Exception:
            return {}

    # ------------------------------------------------------------------ #
    # Registration flow
    # ------------------------------------------------------------------ #
    def register(self, index: int) -> dict:
        # 1. Create mailbox
        step(index, "创建临时邮箱", "cyan")
        prefix = str(config["mail"].get("prefix", "")).strip()
        username = None
        if prefix:
            suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(4, 8)))
            username = f"{prefix}{suffix}"
        self.mailbox = create_mailbox(config["mail"], username=username, proxy=self.proxy)
        email = str(self.mailbox.get("address") or "").strip()
        if not email:
            raise RuntimeError("邮箱服务未返回 address")
        step(index, f"邮箱就绪: {email}", "green")
        jwt = str(self.mailbox.get("token") or "").strip()
        if not jwt:
            raise RuntimeError("邮箱服务未返回 jwt")
        step(index, f"邮箱就绪: {jwt}", "green")
        # step(index, f"JWT: {jwt[:8]}...{jwt[-8:]}" if len(jwt) > 16 else "JWT: <hidden>", "green")
        # 2. Visit invite page (if configured) then login page → get ctoken cookie
        step(index, "获取 ctoken", "cyan")
        invite_code = str(config.get("invite_code") or "").strip()
        if invite_code:
            step(index, f"使用邀请码: {invite_code}", "cyan")
            self.session.get(f"{TARGET_BASE}/invite/{invite_code}", headers={"User-Agent": USER_AGENT}, timeout=15, verify=False)
        self.session.get(f"{TARGET_BASE}/login", headers={"User-Agent": USER_AGENT}, timeout=15, verify=False)
        self.ctoken = str(self.session.cookies.get("ctoken") or "")
        if not self.ctoken:
            raise RuntimeError("未能获取 ctoken cookie")
        step(index, f"ctoken: {self.ctoken}", "green")

        # 3-6. Login (CDP browser or HTTP)
        if self.captcha_cfg.get("provider") == "cdp":
            # CDP browser: full login flow in user's Chrome
            step(index, "CDP 浏览器登录", "cyan")
            from zm_auto.captcha.login import CDPLoginSolver

            cdp_url = self.captcha_cfg.get("browser", {}).get("cdp_url", "http://127.0.0.1:9222")
            invite_code = str(config.get("invite_code") or "").strip()
            login_url = f"{TARGET_BASE}/invite/{invite_code}" if invite_code else f"{TARGET_BASE}/login"
            login_solver = CDPLoginSolver(cdp_url, site_url=TARGET_BASE, invite_code=invite_code)

            def _get_code() -> str | None:
                logger.debug("  (轮询邮箱中，每2秒一次，最长120秒)...")
                code = wait_for_code(config["mail"], self.mailbox, proxy=self.proxy)
                if code:
                    logger.debug(f"  ✓ 邮箱中提取到验证码: {code}")
                else:
                    logger.debug("  ✗ 邮箱轮询超时，未收到验证码")
                    # 兜底：直接查收件箱看原始内容
                    try:
                        from zm_auto.providers import _create_provider, _extract_code
                        p = _create_provider(
                            config["mail"],
                            provider=self.mailbox.get("provider", ""),
                            provider_ref=self.mailbox.get("provider_ref", ""),
                            proxy=self.proxy,
                        )
                        msg = p.fetch_latest_message(self.mailbox)
                        if msg:
                            logger.debug(f"  [DEBUG] 收件箱有消息: subject={msg.get('subject','')[:80]}")
                            logger.debug(f"  [DEBUG] text_content={msg.get('text_content','')[:300]}")
                            logger.debug(f"  [DEBUG] html_content={msg.get('html_content','')[:300]}")
                            retry_code = _extract_code(msg)
                            logger.debug(f"  [DEBUG] _extract_code 结果: {retry_code}")
                            if retry_code:
                                code = retry_code
                        else:
                            logger.debug("  [DEBUG] 收件箱为空，邮件可能未到达")
                        p.close()
                    except Exception as e:
                        logger.debug(f"  [DEBUG] 兜底检查失败: {e}")
                return code

            self._cdp_solver = login_solver
            login_result = login_solver.login(
                login_url, email, _get_code
            )

            # login_result is now a dict: {"cookies": [...], "csrf_token": "..."}
            browser_cookies = login_result.get("cookies", login_result) if isinstance(login_result, dict) else []
            csrf_token = login_result.get("csrf_token", "") if isinstance(login_result, dict) else ""

            # Inject browser session cookies into HTTP session
            for c in browser_cookies:
                self.session.cookies.set(
                    c["name"], c["value"],
                    domain=c.get("domain", ""),
                    path=c.get("path", "/"),
                )
            # CDP 登录后 ctoken 可能已更新，刷新并作为 CSRF token 回退
            self.ctoken = str(self.session.cookies.get("ctoken") or self.ctoken)
            if not csrf_token:
                csrf_token = self.ctoken
            # Store CSRF token for API requests
            self.csrf_token = csrf_token
            step(index, "CDP 登录完成", "green")
        else:
            # HTTP flow: 2captcha / browser provider
            step(index, "解 Turnstile", "cyan")
            turnstile_token = self.captcha.solve_turnstile(f"{TARGET_BASE}/login")
            step(index, f"Turnstile 通过 (len={len(turnstile_token)})", "green")

            step(index, "发送邮箱验证码", "cyan")
            send_resp = self._post(
                "/login/email/code/send",
                payload={"email": email, "token": turnstile_token},
                referer=f"{TARGET_BASE}/login",
            )
            if not send_resp.get("success"):
                raise RuntimeError(f"发送验证码失败: {send_resp}")
            expires_in = send_resp.get("data", {}).get("expiresIn", "?")
            step(index, f"验证码已发送 (有效期 {expires_in}s)", "green")

            step(index, "等待邮箱验证码", "cyan")
            code = wait_for_code(config["mail"], self.mailbox, proxy=self.proxy)
            if not code:
                raise RuntimeError("等待验证码超时")
            step(index, f"收到验证码: {code}", "green")

            step(index, "验证码登录", "cyan")
            verify_resp = self._post(
                "/login/email/code/verify",
                payload={"email": email, "code": code},
                referer=f"{TARGET_BASE}/login",
            )
            if not verify_resp.get("success"):
                raise RuntimeError(f"验证码登录失败: {verify_resp}")
            is_new = bool(verify_resp.get("data", {}).get("isNew"))
            step(index, f"登录成功 (isNew={is_new})", "green")

        # 7. Check user info
        step(index, "获取用户信息", "cyan")
        user_info = self._get("/user/info", referer=f"{TARGET_BASE}/")
        step(index, f"user_info 原始: {json.dumps(user_info, ensure_ascii=False)[:400]}", "cyan")
        user_data = user_info.get("data") or {}
        need_verify = bool(user_data.get("needVerify"))
        user_id = str(user_data.get("userId") or user_data.get("accountId") or "")
        step(index, f"userId={user_id}, needVerify={need_verify}", "green")

        # 8. reCAPTCHA (if needed)
        if need_verify:
            step(index, "解 reCAPTCHA v2", "cyan")
            # Pass session cookies so CDP browser can access the authenticated page
            domain = f".{urlparse(TARGET_BASE).netloc}"
            session_cookies = [
                {"name": str(k), "value": str(v), "domain": domain, "path": "/"}
                for k, v in self.session.cookies.items()
            ]
            recaptcha_token = self.captcha.solve_recaptcha(
                f"{TARGET_BASE}/verify?method=unknown",
                cookies=session_cookies,
            )
            step(index, f"reCAPTCHA 通过 (len={len(recaptcha_token)})", "green")

            # 9. Submit recaptcha verification
            step(index, "提交 reCAPTCHA 验证", "cyan")
            rc_resp = self._post(
                "/login/recaptcha/verification",
                payload={"token": recaptcha_token},
                referer=f"{TARGET_BASE}/verify?method=unknown",
            )
            if not rc_resp.get("success"):
                raise RuntimeError(f"reCAPTCHA 验证失败: {rc_resp}")
            step(index, "reCAPTCHA 验证成功", "green")

            # Re-check user info
            user_info = self._get("/user/info", referer=f"{TARGET_BASE}/")
            user_data = user_info.get("data") or {}
            need_verify = bool(user_data.get("needVerify"))
            if user_data.get("needVerify"):
                raise RuntimeError("reCAPTCHA 后 needVerify 仍为 true")
            step(index, "白名单已解锁", "green")

        # 9.5 Waitlist / whitelist check
        in_white_list = bool(user_data.get("inWhiteList"))
        step(index, f"inWhiteList={in_white_list}, needVerify={need_verify}", "cyan")
        if not in_white_list:
            # Account is not whitelisted (either needVerify or waitlisted)
            if need_verify:
                step(index, "账号需要 reCAPTCHA 验证", "yellow")
            else:
                step(index, "账号未在白名单，已进入 waitlist，无法创建 API Key", "red")
                on_waitlist = str(config.get("on_waitlist") or "abort").lower()
                if on_waitlist == "abort":
                    raise RuntimeError("账号进入 waitlist，未在白名单")
                elif on_waitlist == "skip_create":
                    step(index, "配置 skip_create，跳过 API Key 创建", "yellow")
                    return {
                        "email": email,
                        "user_id": user_id,
                        "api_key": "",
                        "key_name": "",
                        "note": "waitlist",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                # else continue, will likely fail later

        # 10. Create API key
        key_name = str(config.get("api_key_name") or "auto")
        if key_name == "auto":
            key_name = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        step(index, f"创建 API Key (name={key_name})", "cyan")
        create_resp = self._post(
            "/api_key/create",
            payload={"name": key_name, "tags": []},
            referer=f"{TARGET_BASE}/platform/pay-as-you-go",
        )
        create_data = create_resp.get("data") or {}
        api_key = str(create_data.get("token") or create_data.get("key") or "")
        # If the key is masked (e.g. "sk-ai-...a8c9"), fetch the full list
        if not api_key or "*" in api_key:
            step(index, "API Key 被脱敏(***), 从列表接口获取", "yellow")
            list_resp = self._get(
                "/api_key/list",
                referer=f"{TARGET_BASE}/platform/pay-as-you-go",
            )
            keys = list_resp.get("data") or []
            if isinstance(keys, list) and keys:
                # Pick the most recently created key
                latest = keys[0]
                api_key = str(latest.get("token") or latest.get("key") or latest.get("apiKey") or "")
                if not api_key:
                    # Some APIs return the full key only in create, list shows masked
                    api_key = str(create_data.get("token") or create_data.get("key") or "")
        if not api_key:
            step(index, f"创建 API Key 失败: {create_resp}", "red")
            return {
                "email": email,
                "email_provider": str(self.mailbox.get("provider") or ""),
                "email_token": str(self.mailbox.get("token") or ""),
                "user_id": user_id,
                "api_key": "",
                "key_name": key_name,
                "note": f"api_key_create_failed: {create_resp}",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        step(index, f"API Key: {api_key[:12]}...{api_key[-4:]}", "green")

        # 11. Import to Sub2API
        sub2api_cfg = config.get("sub2api", {})
        if sub2api_cfg.get("enabled", False):
            step(index, "导入 Sub2API", "cyan")
            try:
                importer = Sub2APIImporter(sub2api_cfg)
                account_name = f"auto-{email.split('@')[0][:20]}"
                account_data = importer.import_key(api_key, name=account_name)
                sub2api_id = account_data.get("id", "?")
                step(index, f"Sub2API 导入成功 (account id={sub2api_id})", "green")
            except Exception as e:
                step(index, f"Sub2API 导入失败: {e}", "yellow")

        return {
            "email": email,
            "email_provider": str(self.mailbox.get("provider") or ""),
            "email_token": str(self.mailbox.get("token") or ""),
            "user_id": user_id,
            "api_key": api_key,
            "key_name": key_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
