"""⚠️ DISCLAIMER: This project is for educational and research purposes only.

读取已登录 Chrome 浏览器中的 zenmux 用户信息和 API Key。
支持导出为 sub2api 兼容格式。

用法:
  python read_user_info.py                     # 读取全部信息，保存到 user_info.json
  python read_user_info.py --export-sub2api    # 导出 sub2api 兼容格式
  python read_user_info.py --pretty            # 美化打印
  python read_user_info.py -o custom.json      # 指定输出文件
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from curl_cffi import requests as curl_requests
# --create-key / auto-create 状态
_create_key_requested = False
_create_key_name = "auto"
_auto_create_key: bool | None = None  # None=按 config 决定

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"

CDP_URL = "http://127.0.0.1:9222"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
X_API_VERSION = "2026-04-20"


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {}


def get_cdp_url() -> str:
    cfg = load_config()
    return str(cfg.get("captcha", {}).get("browser", {}).get("cdp_url", CDP_URL))


def get_proxy() -> str:
    cfg = load_config()
    return str(cfg.get("proxy", ""))


def get_site_url() -> str:
    """从 config.json 读取目标站点地址。"""
    cfg = load_config()
    return str(cfg.get("site_url", "https://zenmux.ai")).rstrip("/")


def get_site_domain() -> str:
    """返回带点的前缀域名，用于 cookie domain（例如 .zenmux.ai）。"""
    return "." + urlparse(get_site_url()).netloc


# --------------------------------------------------------------------------- #
# CDP helpers
# --------------------------------------------------------------------------- #
def _cdp_connect(cdp_url: str) -> tuple[Any, Any]:
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(cdp_url)
    return pw, browser


def _cdp_new_page(browser: Any) -> Any:
    if browser.contexts:
        return browser.contexts[0].new_page()
    return browser.new_page()


# --------------------------------------------------------------------------- #
# API 调用：方案 A — 页面内 fetch（自动携带 cookies）
# --------------------------------------------------------------------------- #
def _fetch_via_page(page: Any, path: str) -> dict:
    return page.evaluate(
        f"""
        async () => {{
            try {{
                const resp = await fetch("{path}", {{
                    headers: {{
                        "Accept": "application/json",
                        "x-api-version": "{X_API_VERSION}",
                    }},
                    credentials: "include",
                }});
                const text = await resp.text();
                let data;
                try {{ data = JSON.parse(text); }} catch(e) {{ data = text; }}
                return {{ ok: true, status: resp.status, data }};
            }} catch (e) {{
                return {{ ok: false, error: e.message }};
            }}
        }}
        """
    )


# --------------------------------------------------------------------------- #
# API 调用：方案 B — 提取 cookies，Python HTTP 请求
# --------------------------------------------------------------------------- #
def _extract_cookies(page: Any) -> dict[str, str]:
    site_domain = get_site_domain()  # e.g. .zenmux.ai
    bare_domain = site_domain.lstrip(".")  # e.g. zenmux.ai
    return {
        c["name"]: c["value"]
        for c in page.context.cookies()
        if c.get("domain", "").endswith((site_domain, bare_domain))
    }


def _make_http_session(cookies: dict[str, str], proxy: str = "") -> curl_requests.Session:
    session = curl_requests.Session(impersonate="chrome")
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    domain = get_site_domain()
    for name, value in cookies.items():
        session.cookies.set(name, value, domain=domain, path="/")
    return session


def _fetch_via_http(session: curl_requests.Session, path: str) -> dict:
    url = f"{get_site_url()}{path}"
    try:
        resp = session.get(
            url,
            headers={
                "Accept": "application/json",
                "x-api-version": X_API_VERSION,
                "User-Agent": USER_AGENT,
            },
            timeout=30,
            verify=False,
        )
        try:
            data = resp.json()
        except Exception:
            data = resp.text
        return {"ok": True, "status": resp.status_code, "data": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# --------------------------------------------------------------------------- #

def _extract_csrf_token(page: Any) -> str:
    """从页面或 cookies 中提取 CSRF token（用于 API 请求）。"""
    # 1) 页面 meta / window
    try:
        token = page.evaluate(
            """() => {
                const m = document.querySelector('meta[name="csrf-token"]');
                if (m) return m.getAttribute("content") || "";
                const m2 = document.querySelector('meta[name="_csrf"]');
                if (m2) return m2.getAttribute("content") || "";
                return window.csrfToken || window.CSRF_TOKEN || "";
            }"""
        )
        if token:
            return token
    except Exception:
        pass
    # 2) cookies
    try:
        for c in page.context.cookies():
            if c["name"].lower() in ("csrf_token", "_csrf", "xsrf-token", "csrf-token"):
                return c["value"]
        # 部分站点使用 ctoken 作为 CSRF token
        for c in page.context.cookies():
            if c["name"] == "ctoken":
                return c["value"]
    except Exception:
        pass
    return ""


def _extract_ctoken(page: Any) -> str:
    """从 cookies 中提取 ctoken（API 校验需要）。"""
    try:
        for c in page.context.cookies():
            if c["name"] == "ctoken":
                return c["value"]
    except Exception:
        pass
    return ""


def _post_via_page(page: Any, path: str, payload: dict, csrf_token: str = "") -> dict:
    """通过页面内 fetch 发起 POST（自动携带 cookies）。"""
    import json as _json
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-api-version": X_API_VERSION,
    }
    if csrf_token:
        headers["x-csrf-token"] = csrf_token
        headers["x-xsrf-token"] = csrf_token
    headers_json = _json.dumps(headers)
    payload_json = _json.dumps(payload)
    return page.evaluate(
        f"""
        async () => {{
            try {{
                const resp = await fetch("{path}", {{
                    method: "POST",
                    headers: {headers_json},
                    body: JSON.stringify({payload_json}),
                    credentials: "include",
                }});
                const text = await resp.text();
                let data;
                try {{ data = JSON.parse(text); }} catch(e) {{ data = text; }}
                return {{ ok: true, status: resp.status, data: data }};
            }} catch (e) {{
                return {{ ok: false, error: e.message }};
            }}
        }}
        """
    )


def _post_via_http(session: curl_requests.Session, path: str, payload: dict, csrf_token: str = "", ctoken: str = "") -> dict:
    """通过 Python HTTP session 发起 POST。"""
    import urllib.parse as _up
    url = f"{get_site_url()}{path}"
    if ctoken:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}ctoken={_up.quote(ctoken)}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-api-version": X_API_VERSION,
        "User-Agent": USER_AGENT,
    }
    if csrf_token:
        headers["x-csrf-token"] = csrf_token
        headers["x-xsrf-token"] = csrf_token
    try:
        resp = session.post(url, headers=headers, json=payload, timeout=30, verify=False)
        try:
            data = resp.json()
        except Exception:
            data = resp.text
        return {"ok": True, "status": resp.status_code, "data": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# --------------------------------------------------------------------------- #
# 自动创建判断
# --------------------------------------------------------------------------- #
def _should_auto_create_key() -> bool:
    """根据 config 判断是否允许无 key 时自动创建。"""
    if _auto_create_key is not None:
        return _auto_create_key
    cfg = load_config()
    if "auto_create_api_key" in cfg:
        return bool(cfg["auto_create_api_key"])
    # 兼容旧配置：配置了 api_key_name 则认为允许自动创建
    return bool(cfg.get("api_key_name"))

# --------------------------------------------------------------------------- #
# 用户信息读取
# --------------------------------------------------------------------------- #
def _read_user_info(page: Any, session: curl_requests.Session) -> dict | None:
    """尝试多种方式读取用户信息，返回 data dict 或 None。"""
    # 方案 A: 页面内 fetch
    resp = _fetch_via_page(page, "/api/user/info")
    if resp.get("ok"):
        data = resp.get("data", {})
        user_data = data.get("data") if isinstance(data, dict) else None
        if user_data:
            return user_data

    # 方案 B: HTTP
    resp = _fetch_via_http(session, "/api/user/info")
    if resp.get("ok"):
        data = resp.get("data", {})
        user_data = data.get("data") if isinstance(data, dict) else None
        if user_data:
            return user_data

    return None


def _read_api_keys(page: Any, session: curl_requests.Session) -> list[dict]:
    """尝试多种方式读取 API Key 列表。

    注意：/api/api_key/list 返回脱敏 key（sk-ai-...a8c9），
    完整 key 只在创建时返回一次。这里优先从页面 DOM 抓取完整 key。
    """
    # 方案 A: 从 API Keys 管理页面 DOM 抓取完整 key
    dom_keys = _scrape_keys_from_dom(page)
    if dom_keys:
        print(f"  DOM 抓取到 {len(dom_keys)} 个完整 API Key")
        return dom_keys

    # 方案 B: 页面内 fetch（脱敏 key，仅用于记录）
    resp = _fetch_via_page(page, "/api/api_key/list")
    if resp.get("ok") and resp.get("status") == 200:
        data = resp.get("data", {})
        keys = data.get("data") if isinstance(data, dict) else data
        if isinstance(keys, list) and keys:
            print(f"  list API 返回 {len(keys)} 个 key（已脱敏，含 ...）")
            return keys

    # 方案 C: HTTP（脱敏 key，仅用于记录）
    resp = _fetch_via_http(session, "/api/api_key/list")
    if resp.get("ok") and resp.get("status") == 200:
        data = resp.get("data", {})
        keys = data.get("data") if isinstance(data, dict) else data
        if isinstance(keys, list) and keys:
            print(f"  HTTP list API 返回 {len(keys)} 个 key（已脱敏，含 ...）")
            return keys

    return []


def _scrape_keys_from_dom(page: Any) -> list[dict]:
    """导航到 API Keys 管理页面，从 DOM 抓取完整 key。

    策略：
    1. 导航到 /platform/pay-as-you-go
    2. 遍历文本节点查找 sk-ai-xxx（不含 ...）
    3. 查找 input/textarea 中的完整 key
    4. 尝试点击复制按钮触发 key 展示
    """
    try:
        page.goto(f"{get_site_url()}/platform/pay-as-you-go",
                  wait_until="domcontentloaded", timeout=10000)
        time.sleep(2)
    except Exception:
        return []

    # 尝试点击 "复制" 或 "眼睛" 按钮来展示完整 key
    try:
        page.evaluate("""
            () => {
                document.querySelectorAll('button, [role="button"], svg').forEach(el => {
                    const text = (el.textContent || '').toLowerCase();
                    const parent = el.closest('button, [role="button"]');
                    if (text.includes('copy') || text.includes('复制') || text.includes('eye')) {
                        (parent || el).click();
                    }
                });
            }
        """)
        time.sleep(1)
    except Exception:
        pass

    keys = page.evaluate("""
        () => {
            const results = [];
            const seen = new Set();
            // 遍历所有文本节点，查找形如 sk-ai-xxx 的完整 key（不含 ...）
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            let node;
            while (node = walker.nextNode()) {
                const text = (node.textContent || '').trim();
                const match = text.match(/sk-ai-[a-zA-Z0-9]{30,}/);
                if (match && !text.includes('...') && !seen.has(match[0])) {
                    seen.add(match[0]);
                    results.push({ token: match[0], name: '', source: 'dom_text' });
                }
            }
            // 也查找 input/textarea 中的完整 key
            document.querySelectorAll('input, textarea').forEach(el => {
                const val = (el.value || '').trim();
                if (val.startsWith('sk-ai-') && val.length > 30 && !val.includes('...') && !seen.has(val)) {
                    seen.add(val);
                    results.push({ token: val, name: el.getAttribute('placeholder') || '', source: 'dom_input' });
                }
            });
            return results;
        }
    """)
    return keys



# --------------------------------------------------------------------------- #
# sub2api 导出
# --------------------------------------------------------------------------- #

def _build_model_mapping(models: list[str], model_aliases: dict[str, str] | None = None) -> dict[str, str]:
    """构建 model_mapping：配置模型映射到自己，并补充别名映射。
    
    model_aliases 优先于内置默认别名；若未提供则使用内置常见别名。
    """
    mapping: dict[str, str] = {m: m for m in models}
    if model_aliases:
        for alias, target in model_aliases.items():
            if alias not in mapping:
                mapping[alias] = target
    elif models:
        first = models[0]
        for alias in ("gpt-5.5", "gpt-5", "gpt-4", "claude-opus-4-7", "claude-sonnet-4"):
            if alias not in mapping:
                mapping[alias] = first
    return mapping

def _build_sub2api_export(
    api_keys: list[dict],
    user_info: dict | None,
    sub2api_cfg: dict,
) -> list[dict]:
    """将 API Keys 转换为 sub2api 兼容的账号导入格式。"""
    models = sub2api_cfg.get("models", [])
    export_cfg = sub2api_cfg.get("export", {})
    # base_url 从 export 配置读取，空则使用 site_url/api
    site_url = get_site_url()
    base_url = str(export_cfg.get("base_url") or f"{site_url}/api").rstrip("/")
    notes_path = str(export_cfg.get("notes_path", "/v1/chat/completions"))
    concurrency = int(export_cfg.get("concurrency", sub2api_cfg.get("concurrency", 3)))
    responses_supported = bool(export_cfg.get("openai_responses_supported", True))
    responses_mode = str(export_cfg.get("openai_responses_mode", "force_chat_completions"))

    model_mapping = _build_model_mapping(models, export_cfg.get("model_aliases", {}))

    accounts = []
    for key in api_keys:
        token = key.get("token") or key.get("key") or ""
        name = key.get("name", "")
        email = user_info.get("email", "") if user_info else ""

        accounts.append({
            "name": name or f"zenmux-{token[-6:]}" if token else "unknown",
            "notes": f"{base_url}{notes_path}",
            "platform": "openai",
            "type": "apikey",
            "credentials": {
                "api_key": token,
                "base_url": base_url,
                "model_mapping": model_mapping,
                "openai_capabilities": ["chat_completions"],
            },
            "extra": {
                "openai_apikey_responses_websockets_v2_enabled": False,
                "openai_apikey_responses_websockets_v2_mode": "off",
                "openai_compact_mode": "force_off",
                "openai_responses_mode": responses_mode,
                "openai_responses_supported": responses_supported,
            },
            "concurrency": concurrency,
            "priority": 51,
            "rate_multiplier": 1,
            "auto_pause_on_expired": True,
            # 附加元数据
            "source": "zenmux",
            "user_email": email,
            "user_id": user_info.get("userId", "") if user_info else "",
        })

    return accounts


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #

def create_api_key(page: Any, session: curl_requests.Session, name: str = "") -> dict | None:
    """通过 API 自动创建 API Key 并返回完整 token。

    优先调用 /api/api_key/create；若响应被脱敏，则回退到 list 接口取最新 key。
    名称来源：参数 > config.api_key_name（auto 则随机）> 随机字符串。
    """
    import random, string

    if not name or name == "auto":
        cfg_name = str(load_config().get("api_key_name") or "")
        if cfg_name and cfg_name != "auto":
            name = cfg_name
        else:
            name = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

    print(f"{_ts()} 未找到 API Key，尝试自动创建 (name={name})...")

    csrf_token = _extract_csrf_token(page)
    ctoken = _extract_ctoken(page)
    payload = {"name": name, "tags": []}

    # 1) 页面内 fetch 创建（cookie 自动携带，最稳）
    resp = _post_via_page(page, "/api/api_key/create", payload, csrf_token)
    if not resp.get("ok") and resp.get("status") not in (200, 201):
        print(f"{_ts()} 页面 fetch 创建失败: {resp.get('error')}")
        resp = _post_via_http(session, "/api/api_key/create", payload, csrf_token, ctoken)

    if not resp.get("ok") and resp.get("status") not in (200, 201):
        print(f"{_ts()} 创建 API Key 失败: {resp.get('error')}")
        return None

    raw = resp.get("data", {}) or {}
    token = ""
    if isinstance(raw, dict):
        # 直接返回的 data
        token = str(raw.get("token") or raw.get("key") or "")
        name = raw.get("name") or name
        # 嵌套 data: {success, data: {token, ...}}
        if not token and isinstance(raw.get("data"), dict):
            inner = raw["data"]
            token = str(inner.get("token") or inner.get("key") or "")
            name = inner.get("name") or name

    # 2) 如果返回的是脱敏 key，尝试从 list 拿最新的
    if not token or "*" in token or "..." in token or len(token) < 20:
        print(f"{_ts()} 创建响应未返回完整 key，尝试从列表获取...")
        latest = _read_api_keys(page, session)
        if latest:
            first = latest[0]
            token = first.get("token") or first.get("key") or ""
            name = first.get("name") or name

    if token and token.startswith("sk-ai-") and len(token) > 30 and "*" not in token and "..." not in token:
        print(f"{_ts()} 创建成功: {name} -> {token[:20]}...{token[-8:]}")
        return {"name": name, "token": token, "source": "created"}

    print(f"{_ts()} ⚠ 创建 API Key 后未获取到完整 token")
    return None

def read_user_info(cdp_url: str = "") -> dict:
    cdp_url = cdp_url or get_cdp_url()
    proxy = get_proxy()

    print(f"{_ts()} 连接 Chrome (CDP: {cdp_url})...")
    try:
        pw, browser = _cdp_connect(cdp_url)
    except Exception as e:
        print(f"{_ts()} 连接失败: {e}")
        _print_chrome_hint()
        sys.exit(1)

    page = _cdp_new_page(browser)
    result: dict[str, Any] = {
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "cdp_url": cdp_url,
    }

    try:
        # 导航到平台页面
        site_url = get_site_url()
        print(f"{_ts()} 导航到 {site_url}...")
        try:
            page.goto(f"{site_url}/platform", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass

        current_url = page.url
        print(f"{_ts()} 当前页面: {current_url}")
        result["page_url"] = current_url

        if "login" in current_url:
            print(f"\n{_ts()} 当前未登录，请在 Chrome 中登录后重试。")
            pw.stop()
            sys.exit(1)

        if "waitlist" in current_url:
            print(f"{_ts()} 账号在 waitlist 中。")

        # 提取 cookies，创建 HTTP session
        cookies = _extract_cookies(page)
        session = _make_http_session(cookies, proxy)
        result["zenmux_cookies"] = {k: v[:40] + "..." if len(v) > 40 else v for k, v in cookies.items()}

        # 读取用户信息
        print(f"{_ts()} 读取用户信息...")
        user_info = _read_user_info(page, session)
        if user_info:
            result["user_info"] = user_info
            print(f"  userId: {user_info.get('userId', '?')}")
            print(f"  email:  {user_info.get('email', '?')}")
            print(f"  needVerify: {user_info.get('needVerify', '?')}")
        else:
            print(f"  ⚠ 未能获取用户信息（会话可能未登录）")

        # 读取 API Keys（若不存在则创建）
        print(f"{_ts()} 读取 API Keys...")
        api_keys = _read_api_keys(page, session)
        if not api_keys and (_create_key_requested or _should_auto_create_key()):
            print(f"{_ts()} 未找到 API Key，尝试创建...")
            new_key = create_api_key(page, session, _create_key_name)
            if new_key:
                api_keys = [new_key]
        result["api_keys"] = api_keys
        if api_keys:
            print(f"  共 {len(api_keys)} 个 API Key:")
            for k in api_keys:
                name = k.get("name", "?")
                token = k.get("token", k.get("key", "?"))
                masked = str(token)[:16] + "..." if len(str(token)) > 20 else token
                print(f"    - {name}: {masked}")
        else:
            print(f"  未找到 API Key（可能未登录或未创建）")

        # CSRF token
        try:
            csrf = page.evaluate(
                """() => {
                    const m = document.querySelector('meta[name="csrf-token"]');
                    return m ? m.getAttribute("content") : "";
                }"""
            )
            if csrf:
                result["csrf_token"] = csrf
        except Exception:
            pass

    finally:
        page.close()
        pw.stop()

    return result


# --------------------------------------------------------------------------- #
# 导出
# --------------------------------------------------------------------------- #
def export_sub2api(result: dict, output_path: str = "") -> Path:
    """将 API Keys 导入 sub2api 服务器，并保存 JSON 记录。

    流程：读取 config.json sub2api 配置 → 调用 Sub2APIImporter 导入每个 key
    → 保存导入记录到 sub2api_export.json（数组，可追加，按 api_key 去重）。
    """
    cfg = load_config()
    sub2api_cfg = cfg.get("sub2api", {})
    if not sub2api_cfg.get("enabled") and not sub2api_cfg.get("base_url"):
        print(f"{_ts()} sub2api 未启用或未配置 base_url，仅导出 JSON")
        return _save_sub2api_json(result, output_path)

    api_keys = result.get("api_keys", [])
    user_info = result.get("user_info")

    if not api_keys:
        print(f"{_ts()} ⚠ 没有 API Key 可导入")
        return Path()

    # 调用 Sub2APIImporter 真正导入
    importer = Sub2APIImporter(sub2api_cfg)
    imported: list[dict] = []
    failed: list[dict] = []

    for key in api_keys:
        token = key.get("token") or key.get("key") or ""
        name = key.get("name", "")
        email = user_info.get("email", "") if user_info else ""
        account_name = name or f"zenmux-{email.split('@')[0][:20]}" if email else f"zenmux-{token[-6:]}"

        try:
            account_data = importer.import_key(token, name=account_name)
            sub2api_id = account_data.get("id", "?")
            print(f"{_ts()}   导入成功: {account_name} (sub2api id={sub2api_id})")
            export_cfg = sub2api_cfg.get("export", {})
            base_url = str(export_cfg.get("base_url") or f"{get_site_url()}/api").rstrip("/")
            notes_path = str(export_cfg.get("notes_path", "/v1/chat/completions"))
            concurrency = int(export_cfg.get("concurrency", sub2api_cfg.get("concurrency", 3)))
            responses_supported = bool(export_cfg.get("openai_responses_supported", True))
            responses_mode = str(export_cfg.get("openai_responses_mode", "force_chat_completions"))
            model_mapping = _build_model_mapping(sub2api_cfg.get("models", []), export_cfg.get("model_aliases", {}))

            imported.append(_build_import_record({
                "name": account_name,
                "notes": f"{base_url}{notes_path}",
                "platform": "openai",
                "type": "apikey",
                "credentials": {
                    "api_key": token,
                    "base_url": base_url,
                    "model_mapping": model_mapping,
                    "openai_capabilities": ["chat_completions"],
                },
                "extra": {
                    "openai_apikey_responses_websockets_v2_enabled": False,
                    "openai_apikey_responses_websockets_v2_mode": "off",
                    "openai_compact_mode": "force_off",
                    "openai_responses_mode": responses_mode,
                    "openai_responses_supported": responses_supported,
                },
                "concurrency": concurrency,
                "priority": 51,
                "rate_multiplier": 1,
                "auto_pause_on_expired": True,
                "source": "zenmux",
                "user_email": email,
                "user_id": user_info.get("userId", "") if user_info else "",
            }, sub2api_id))
        except Exception as e:
            print(f"{_ts()}   导入失败: {account_name} — {e}")
            failed.append({"name": account_name, "credentials": {"api_key": token}, "error": str(e)})

    # 保存导入记录到 JSON（追加模式）
    out_path = Path(output_path) if output_path else (BASE_DIR / "sub2api_export.json")
    _append_json_records(out_path, imported)
    print(f"{_ts()} sub2api 导入完成: 成功 {len(imported)}，失败 {len(failed)}，记录已保存到 {out_path}")
    return out_path


def _save_sub2api_json(result: dict, output_path: str = "") -> Path:
    """仅导出 JSON 记录（不调用 sub2api 服务器）。"""
    cfg = load_config()
    sub2api_cfg = cfg.get("sub2api", {})
    api_keys = result.get("api_keys", [])
    user_info = result.get("user_info")
    accounts = _build_sub2api_export(api_keys, user_info, sub2api_cfg)
    out_path = Path(output_path) if output_path else (BASE_DIR / "sub2api_export.json")
    _append_json_records(out_path, accounts)
    print(f"{_ts()} 仅导出 JSON: {out_path} ({len(accounts)} 个账号)")
    return out_path


def _build_import_record(account: dict, sub2api_id: str = "") -> dict:
    """将 sub2api 导入结果转为与 export 一致的记录格式。"""
    record = dict(account)
    record["imported_at"] = datetime.now(timezone.utc).isoformat()
    if sub2api_id:
        record["sub2api_id"] = sub2api_id
    return record


def _append_json_records(out_path: Path, new_records: list[dict]) -> None:
    """追加记录到 sub2api_export.json，按 api_key 去重。

    文件格式（sub2api 兼容导入格式）:
      {
        "exported_at": "2026-06-18T17:34:53Z",
        "proxies": [],
        "accounts": [account1, account2, ...]
      }
    """
    existing_accounts: list[dict] = []
    if out_path.exists():
        try:
            loaded = json.loads(out_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and "accounts" in loaded:
                existing_accounts = loaded.get("accounts", [])
            elif isinstance(loaded, list):
                # 兼容旧格式：纯数组
                existing_accounts = loaded
        except Exception:
            existing_accounts = []

    if not isinstance(existing_accounts, list):
        existing_accounts = []

    # 按 api_key 去重
    existing_keys = {a.get("credentials", {}).get("api_key", "") for a in existing_accounts}
    to_add = []
    for r in new_records:
        key = r.get("credentials", {}).get("api_key", "")
        if key and key not in existing_keys:
            to_add.append(r)
            existing_keys.add(key)

    existing_accounts.extend(to_add)

    # 输出 sub2api 兼容的导入格式
    export_data = {
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "proxies": [],
        "accounts": existing_accounts,
    }
    out_path.write_text(json.dumps(export_data, ensure_ascii=False, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _print_chrome_hint() -> None:
    print("\n请确保 Chrome 已启动:")
    print('  open -a "Google Chrome" --args \\')
    print('    --remote-debugging-port=9222 \\')
    print('    --proxy-server="http://127.0.0.1:7890" \\')
    print('    --user-data-dir=/tmp/chrome-cdp')


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="读取已登录 zenmux 的用户信息和 API Key")
    parser.add_argument("--cdp-url", type=str, default="", help="CDP 连接地址")
    parser.add_argument("-o", "--output", type=str, default="", help="输出 JSON 文件路径")
    parser.add_argument("--export-sub2api", action="store_true", help="导出 sub2api 兼容格式")
    parser.add_argument("--export-sub2api-output", type=str, default="", help="sub2api 导出文件路径")
    parser.add_argument("--pretty", action="store_true", help="美化打印 JSON 到 stdout")
    parser.add_argument("--api-keys-only", action="store_true", help="只读取 API Keys")
    parser.add_argument("--user-only", action="store_true", help="只读取用户信息")
    parser.add_argument("--create-key", type=str, nargs="?", const="auto", metavar="NAME",
                        help="若不存在 API Key 则自动创建，可指定名称（默认 auto）")
    parser.add_argument("--auto-create-key", action="store_true", dest="auto_create_key",
                        help="无 API Key 时自动创建（覆盖 config）")
    parser.add_argument("--no-auto-create-key", action="store_true", dest="no_auto_create_key",
                        help="禁止无 API Key 时自动创建")
    args = parser.parse_args()

    if args.create_key:
        global _create_key_requested, _create_key_name
        _create_key_requested = True
        _create_key_name = args.create_key

    if args.auto_create_key or args.no_auto_create_key:
        global _auto_create_key
        if args.no_auto_create_key:
            _auto_create_key = False
        else:
            _auto_create_key = True
    result = read_user_info(cdp_url=args.cdp_url)

    # 保存完整结果
    out_path = Path(args.output) if args.output else (BASE_DIR / "user_info.json")
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{_ts()} 结果已保存: {out_path}")

    # 导出 sub2api 格式
    if args.export_sub2api:
        export_sub2api(result, args.export_sub2api_output)

    # 美化打印
    if args.pretty:
        print("\n" + "=" * 60)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
