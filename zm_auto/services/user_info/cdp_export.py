from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from curl_cffi import requests as curl_requests

from zm_auto.config import load_config
from zm_auto.constants import CDP_URL, USER_AGENT, X_API_VERSION


def get_cdp_url() -> str:
    return str(load_config().captcha.browser.cdp_url or CDP_URL)


def get_proxy() -> str:
    return str(load_config().proxy or "")


def get_site_url() -> str:
    """从 config.json 读取目标站点地址。"""
    return str(load_config().site_url).rstrip("/")


def get_site_domain() -> str:
    """返回带点的前缀域名，用于 cookie domain（例如 .zenmux.ai）。"""
    return "." + urlparse(get_site_url()).netloc


def _fetch_via_page(page: Any, path: str) -> Any:
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


def _make_http_session(cookies: dict[str, str], proxy: str = "") -> curl_requests.Session:
    session: curl_requests.Session = curl_requests.Session(impersonate="chrome")
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


def _extract_csrf_token(page: Any) -> Any:
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


def _extract_ctoken(page: Any) -> Any:
    """从 cookies 中提取 ctoken（API 校验需要）。"""
    try:
        for c in page.context.cookies():
            if c["name"] == "ctoken":
                return c["value"]
    except Exception:
        pass
    return ""


def _post_via_page(page: Any, path: str, payload: dict, csrf_token: str = "", ctoken: str = "") -> Any:
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
    # 与 HTTP 版本保持一致，把 ctoken 附加到 URL 查询参数
    import urllib.parse as _up
    if ctoken:
        sep = "&" if "?" in path else "?"
        url = f"{path}{sep}ctoken={_up.quote(ctoken)}"
    else:
        url = path
    return page.evaluate(
        f"""
        async () => {{
            try {{
                const resp = await fetch("{url}", {{
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


def _post_via_http(session: curl_requests.Session, path: str, payload: dict, csrf_token: str = "", ctoken: str = "") -> Any:
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


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")
