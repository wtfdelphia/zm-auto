"""诊断 zenmux 账号当前状态：是否登录、是否 needVerify、能否创建 API Key。"""
from __future__ import annotations

import json
import sys
import time
from playwright.sync_api import sync_playwright

X_API_VERSION = "2026-04-20"
CDP_URL = "http://127.0.0.1:9222"


def load_config():
    try:
        with open("config.json") as f:
            return json.load(f)
    except Exception:
        return {}


def get_cdp_url():
    cfg = load_config()
    return cfg.get("captcha", {}).get("browser", {}).get("cdp_url", CDP_URL)


def get_proxy():
    cfg = load_config()
    return cfg.get("proxy", "")


def get_site_url():
    cfg = load_config()
    return str(cfg.get("site_url", "https://zenmux.ai")).rstrip("/")


def main():
    cdp_url = get_cdp_url()
    proxy = get_proxy()
    print(f"连接 CDP: {cdp_url}")
    print(f"代理: {proxy or '无'}")

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(cdp_url)
        if browser.contexts:
            page = browser.contexts[0].new_page()
        else:
            page = browser.new_page()

        # 1. 当前页面
        page.goto(f"{get_site_url()}/platform", wait_until="domcontentloaded", timeout=15000)
        current_url = page.url
        print(f"\n当前页面: {current_url}")

        if "login" in current_url:
            print("❌ 未登录，请先登录")
            return

        # 2. /api/user/info
        print("\n--- /api/user/info ---")
        info = page.evaluate(
            f"""
            async () => {{
                const r = await fetch('/api/user/info', {{
                    headers: {{'Accept': 'application/json', 'x-api-version': '{X_API_VERSION}'}},
                    credentials: 'include'
                }});
                return r.json();
            }}
            """
        )
        print(json.dumps(info, ensure_ascii=False, indent=2))
        user_data = (info or {}).get("data", {}) if isinstance(info, dict) else {}
        need_verify = bool(user_data.get("needVerify"))
        user_id = user_data.get("userId", "")
        email = user_data.get("email", "")
        in_white_list = bool(user_data.get("inWhiteList"))
        print(f"needVerify={need_verify}, inWhiteList={in_white_list}, userId={user_id}, email={email}")
        if not in_white_list and not need_verify:
            print("⚠️  账号未在白名单，已进入 waitlist，无法创建 API Key")
        elif in_white_list:
            print("✅ 账号在白名单内")
        elif need_verify:
            print("🔒 账号需要 reCAPTCHA 验证")

        # 3. 检查 /verify 页面是否有 reCAPTCHA
        if need_verify:
            print("\n--- 访问 /verify 检查 reCAPTCHA ---")
            page.goto(f"{get_site_url()}/verify?method=unknown", wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            recaptcha_exists = page.evaluate("""() => {
                return !!document.querySelector('.g-recaptcha, iframe[src*=\"recaptcha\"], #g-recaptcha-response');
            }""")
            print(f"页面存在 reCAPTCHA widget: {recaptcha_exists}")
            print(f"当前 URL: {page.url}")

            # 检查页面文本
            body_text = page.evaluate("() => document.body.innerText")
            if body_text:
                print(f"页面文本片段: {body_text[:200]}...")

        # 4. 尝试 /api/api_key/list（看权限）
        print("\n--- /api/api_key/list ---")
        try:
            list_resp = page.evaluate(
                f"""
                async () => {{
                    const r = await fetch('/api/api_key/list', {{
                        headers: {{'Accept': 'application/json', 'x-api-version': '{X_API_VERSION}'}},
                        credentials: 'include'
                    }});
                    const text = await r.text();
                    let body = null;
                    try {{ body = JSON.parse(text); }} catch (e) {{ body = null; }}
                    return {{status: r.status, body: body, text: text}};
                }}
                """
            )
            print(json.dumps(list_resp, ensure_ascii=False, indent=2)[:500])
        except Exception as e:
            print(f"失败: {e}")

        page.close()
        print("\n诊断完成。")


if __name__ == "__main__":
    main()
