"""⚠️ DISCLAIMER: This project is for educational and research purposes only.
Users are solely responsible for complying with all applicable ToS and laws.
本项目仅供学习研究，使用者需自行承担所有后果。
"""

from __future__ import annotations

import json
import random
import string
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import urllib3
from urllib.parse import urlparse
from curl_cffi import requests as curl_requests

from mail_provider import create_mailbox, wait_for_code
from captcha_solver import CaptchaSolver
from sub2api_importer import Sub2APIImporter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"

X_API_VERSION = "2026-04-20"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

print_lock = threading.Lock()
stats_lock = threading.Lock()
stats = {"done": 0, "success": 0, "fail": 0, "start_time": 0.0}


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
DEFAULT_CONFIG: dict[str, Any] = {
    "mail": {
        "request_timeout": 30,
        "wait_timeout": 120,
        "wait_interval": 3,
        "prefix": "",
        "user_agent": USER_AGENT,
        "providers": [],
    },
    "proxy": "",
    "total": 1,
    "threads": 1,
    "captcha": {
        "provider": "2captcha",
        "api_key": "",
        "browser": {
            "headless": True,
            "stealth": True,
            "cdp_url": "http://127.0.0.1:9222"
        },
    },
    "api_key_name": "auto",
    "site_url": "https://zenmux.ai",
    "invite_code": "",
    "logout_after": True,
    "on_waitlist": "abort",  # "abort" | "skip_create" | "continue"
    "waitlist_logout": True,
    "sub2api": {
        "enabled": False,
        "base_url": "",
        "email": "",
        "password": "",
        "group_name": "auto",
        "concurrency": 3,
        "models": ["z-ai/glm-5.2-free", "moonshotai/kimi-k2.7-code-free"],
        "upstream_base_url": "https://example.com/api/anthropic",
    },
}


def load_config() -> dict:
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    if CONFIG_FILE.exists():
        saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        for key in ("mail", "proxy", "total", "threads", "captcha", "api_key_name", "sub2api", "site_url", "invite_code", "logout_after", "on_waitlist", "waitlist_logout"):
            if key in saved:
                config[key] = saved[key]
    return config


config = load_config()
TARGET_BASE = str(config.get("site_url", "https://zenmux.ai")).rstrip("/")
API_BASE = f"{TARGET_BASE}/api"

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def log(text: str, color: str = "") -> None:
    colors = {"red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m", "cyan": "\033[36m"}
    with print_lock:
        prefix = colors.get(color, "")
        suffix = "\033[0m" if prefix else ""
        print(f"{prefix}{datetime.now().strftime('%H:%M:%S')} {text}{suffix}", flush=True)


def step(index: int, text: str, color: str = "") -> None:
    log(f"[任务{index}] {text}", color)


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #
def _make_session(proxy: str = "") -> curl_requests.Session:
    session = curl_requests.Session(impersonate="chrome")
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    return session


def _api_headers(referer: str = "") -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "x-api-version": X_API_VERSION,
        "User-Agent": USER_AGENT,
    }
    if referer:
        headers["Referer"] = referer
    return headers


class Registrar:
    """Handles one full registration attempt — pure HTTP."""

    def __init__(self, proxy: str = "", captcha_cfg: dict | None = None):
        self.proxy = proxy
        self.captcha_cfg = captcha_cfg or {}
        self.session = _make_session(proxy)
        self.ctoken = ""
        self.csrf_token = ""
        self._cdp_solver = None
        self.solver: CaptchaSolver | None = None
        self.mailbox: dict[str, Any] = {}

    def close(self) -> None:
        try:
            if self.solver:
                self.solver.close()
        except Exception:
            pass
        try:
            self.session.close()
        except Exception:
            pass
        try:
            if self._cdp_solver and config.get("logout_after", True):
                self._cdp_solver.logout()
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
            from cdp_solver import CDPLoginSolver

            cdp_url = self.captcha_cfg.get("browser", {}).get("cdp_url", "http://127.0.0.1:9222")
            invite_code = str(config.get("invite_code") or "").strip()
            login_url = f"{TARGET_BASE}/invite/{invite_code}" if invite_code else f"{TARGET_BASE}/login"
            login_solver = CDPLoginSolver(cdp_url, site_url=TARGET_BASE, invite_code=invite_code)

            def _get_code() -> str | None:
                import sys, json
                print("  (轮询邮箱中，每2秒一次，最长120秒)...", flush=True)
                code = wait_for_code(config["mail"], self.mailbox, proxy=self.proxy)
                if code:
                    print(f"  ✓ 邮箱中提取到验证码: {code}", flush=True)
                else:
                    print("  ✗ 邮箱轮询超时，未收到验证码", flush=True)
                    # 兜底：直接查收件箱看原始内容
                    try:
                        from mail_provider import _create_provider, _extract_code
                        p = _create_provider(
                            config["mail"],
                            provider=self.mailbox.get("provider", ""),
                            provider_ref=self.mailbox.get("provider_ref", ""),
                            proxy=self.proxy,
                        )
                        msg = p.fetch_latest_message(self.mailbox)
                        if msg:
                            print(f"  [DEBUG] 收件箱有消息: subject={msg.get('subject','')[:80]}", flush=True)
                            print(f"  [DEBUG] text_content={msg.get('text_content','')[:300]}", flush=True)
                            print(f"  [DEBUG] html_content={msg.get('html_content','')[:300]}", flush=True)
                            retry_code = _extract_code(msg)
                            print(f"  [DEBUG] _extract_code 结果: {retry_code}", flush=True)
                            if retry_code:
                                code = retry_code
                        else:
                            print("  [DEBUG] 收件箱为空，邮件可能未到达", flush=True)
                        p.close()
                    except Exception as e:
                        print(f"  [DEBUG] 兜底检查失败: {e}", flush=True)
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
            # Store CSRF token for API requests
            self.csrf_token = csrf_token
            step(index, "CDP 登录完成", "green")

            # Logout from browser to clean session for next registration
            if config.get("logout_after", True):
                try:
                    login_solver.logout()
                except Exception:
                    pass
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
            raise RuntimeError(f"创建 API Key 失败: {create_resp}")
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
            "user_id": user_id,
            "api_key": api_key,
            "key_name": key_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }


# --------------------------------------------------------------------------- #
# Worker / runner
# --------------------------------------------------------------------------- #
def worker(index: int) -> dict:
    start = time.time()
    registrar = Registrar(
        proxy=config.get("proxy", ""),
        captcha_cfg=config.get("captcha", {}),
    )
    try:
        step(index, "任务启动", "cyan")
        result = registrar.register(index)
        cost = time.time() - start
        with stats_lock:
            stats["done"] += 1
            stats["success"] += 1
            avg = (time.time() - stats["start_time"]) / max(stats["success"], 1)
        log(
            f'{result["email"]} 注册成功，耗时{cost:.1f}s，平均{avg:.1f}s/个，'
            f'API Key: {result["api_key"][:12]}...{result["api_key"][-4:]}',
            "green",
        )
        return {"ok": True, "index": index, "result": result}
    except Exception as e:
        cost = time.time() - start
        with stats_lock:
            stats["done"] += 1
            stats["fail"] += 1
        log(f"任务{index} 注册失败，耗时{cost:.1f}s，原因: {e}", "red")
        return {"ok": False, "index": index, "error": str(e)}
    finally:
        registrar.close()


def run(total: int | None = None, threads: int | None = None) -> list[dict]:
    total = total if total is not None else config.get("total", 1)
    threads = threads if threads is not None else config.get("threads", 1)
    threads = max(1, min(threads, total))

    stats["start_time"] = time.time()
    log(f"开始注册 {total} 个账号，并发 {threads}", "cyan")

    results: list[dict] = []
    if threads == 1:
        for i in range(1, total + 1):
            results.append(worker(i))
    else:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=threads) as pool:
            futures = {pool.submit(worker, i): i for i in range(1, total + 1)}
            for future in as_completed(futures):
                results.append(future.result())

    elapsed = time.time() - stats["start_time"]
    success = sum(1 for r in results if r.get("ok"))
    log(
        f"完成: {success}/{total} 成功，{total - success} 失败，总耗时 {elapsed:.1f}s",
        "green" if success == total else "yellow",
    )

    save_results(results)
    return results


def save_results(results: list[dict]) -> Path:
    out_file = BASE_DIR / "accounts.json"
    existing: list = []
    if out_file.exists():
        try:
            existing = json.loads(out_file.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except Exception:
            existing = []
    for r in results:
        if r.get("ok") and r.get("result"):
            existing.append(r["result"])
    out_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"结果已保存到 {out_file}", "cyan")
    return out_file


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="自动注册机 (纯 HTTP + 2captcha / 浏览器)")
    parser.add_argument("-n", "--total", type=int, help="注册数量")
    parser.add_argument("-t", "--threads", type=int, help="并发数")
    parser.add_argument("--proxy", type=str, help="代理地址")
    args = parser.parse_args()

    if args.total is not None:
        config["total"] = args.total
    if args.threads is not None:
        config["threads"] = args.threads
    if args.proxy:
        config["proxy"] = args.proxy

    run()


if __name__ == "__main__":
    main()
