from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import time
from typing import Any

from curl_cffi import requests as curl_requests

from zm_auto.config import load_config
from zm_auto.sites import get_site_adapter
from zm_auto.services.user_info.cdp_export import (
    _extract_csrf_token,
    _extract_ctoken,
    _fetch_via_http,
    _fetch_via_page,
    _post_via_http,
    _post_via_page,
    _ts,
)
from zm_auto.services.user_info.cdp_export import get_site_url

def _should_auto_create_key(auto_create_key: bool | None = None) -> bool:
    """根据 config 判断是否允许无 key 时自动创建。"""
    if auto_create_key is not None:
        return auto_create_key
    if load_config().auto_create_api_key:
        return True
    # 兼容旧配置：配置了 api_key_name 则认为允许自动创建
    return bool(load_config().api_key_name)

def _read_user_info(page: Any, session: curl_requests.Session) -> Any:
    """尝试多种方式读取用户信息，返回 data dict 或 None。"""
    # 方案 A: 页面内 fetch
    adapter = get_site_adapter()
    resp = _fetch_via_page(page, adapter.user_info_path())
    if resp.get("ok"):
        data = resp.get("data", {})
        user_data = data.get("data") if isinstance(data, dict) else None
        if user_data:
            return user_data

    # 方案 B: HTTP
    adapter = get_site_adapter()
    resp = _fetch_via_http(session, adapter.user_info_path())
    if resp.get("ok"):
        data = resp.get("data", {})
        user_data = data.get("data") if isinstance(data, dict) else None
        if user_data:
            return user_data

    return None

def _read_api_keys(page: Any, session: curl_requests.Session) -> Any:
    """尝试多种方式读取 API Key 列表。

    注意：/api/api_key/list 返回脱敏 key（sk-ai-...a8c9），
    完整 key 只在创建时返回一次。这里优先从页面 DOM 抓取完整 key。
    """
    # 方案 A: 从 API Keys 管理页面 DOM 抓取完整 key
    dom_keys = _scrape_keys_from_dom(page)
    if dom_keys:
        logger.info(f"  DOM 抓取到 {len(dom_keys)} 个完整 API Key")
        return dom_keys

    # 方案 B: 页面内 fetch（脱敏 key，仅用于记录）
    adapter = get_site_adapter()
    resp = _fetch_via_page(page, adapter.api_key_list_path())
    if resp.get("ok") and resp.get("status") == 200:
        data = resp.get("data", {})
        keys = data.get("data") if isinstance(data, dict) else data
        if isinstance(keys, list) and keys:
            logger.info(f"  list API 返回 {len(keys)} 个 key（已脱敏，含 ...）")
            return keys

    # 方案 C: HTTP（脱敏 key，仅用于记录）
    adapter = get_site_adapter()
    resp = _fetch_via_http(session, adapter.api_key_list_path())
    if resp.get("ok") and resp.get("status") == 200:
        data = resp.get("data", {})
        keys = data.get("data") if isinstance(data, dict) else data
        if isinstance(keys, list) and keys:
            logger.info(f"  HTTP list API 返回 {len(keys)} 个 key（已脱敏，含 ...）")
            return keys

    return []

def _scrape_keys_from_dom(page: Any) -> Any:
    """导航到 API Keys 管理页面，从 DOM 抓取完整 key。

    策略：
    1. 导航到 /platform/pay-as-you-go
    2. 遍历文本节点查找 sk-ai-xxx（不含 ...）
    3. 查找 input/textarea 中的完整 key
    4. 尝试点击复制按钮触发 key 展示
    """
    try:
        adapter = get_site_adapter()
        page.goto(f"{get_site_url()}{adapter.api_key_page_path()}",
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

def create_api_key(page: Any, session: curl_requests.Session, name: str = "") -> dict | None:
    """通过 API 自动创建 API Key 并返回完整 token。

    优先调用 /api/api_key/create；若响应被脱敏，则回退到 list 接口取最新 key。
    名称来源：参数 > config.api_key_name（auto 则随机）> 随机字符串。
    """
    import random
    import string

    if not name or name == "auto":
        cfg_name = str(load_config().api_key_name or "")
        if cfg_name and cfg_name != "auto":
            name = cfg_name
        else:
            name = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

    logger.info(f"{_ts()} 未找到 API Key，尝试自动创建 (name={name})...")

    csrf_token = _extract_csrf_token(page)
    ctoken = _extract_ctoken(page)
    payload = {"name": name, "tags": []}

    # 1) 页面内 fetch 创建（cookie 自动携带，最稳）
    adapter = get_site_adapter()
    resp = _post_via_page(page, adapter.register_endpoints().get("create_key", "/api/api_key/create"), payload, csrf_token)
    if not resp.get("ok") and resp.get("status") not in (200, 201):
        logger.info(f"{_ts()} 页面 fetch 创建失败: {resp.get('error')}")
        resp = _post_via_http(session, adapter.register_endpoints().get("create_key", "/api/api_key/create"), payload, csrf_token, ctoken)

    if not resp.get("ok") and resp.get("status") not in (200, 201):
        logger.info(f"{_ts()} 创建 API Key 失败: {resp.get('error')}")
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
        logger.info(f"{_ts()} 创建响应未返回完整 key，尝试从列表获取...")
        latest = _read_api_keys(page, session)
        if latest:
            first = latest[0]
            token = first.get("token") or first.get("key") or ""
            name = first.get("name") or name

    if token and token.startswith("sk-ai-") and len(token) > 30 and "*" not in token and "..." not in token:
        logger.info(f"{_ts()} 创建成功: {name} -> {token[:20]}...{token[-8:]}")
        return {"name": name, "token": token, "source": "created"}

    logger.info(f"{_ts()} ⚠ 创建 API Key 后未获取到完整 token")
    return None
