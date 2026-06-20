"""读取已登录 Chrome 浏览器中的 zenmux 用户信息和 API Key。"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from zm_auto.cdp.helpers import _extract_cookies
from zm_auto.cdp.session import CDPSession
from zm_auto.constants import BASE_DIR
from zm_auto.exceptions import ZMError
from zm_auto.services.user_info.core import (
    _read_api_keys,
    _read_user_info,
    _should_auto_create_key,
    create_api_key,
)
from zm_auto.services.user_info.export import export_sub2api
from zm_auto.services.user_info.cdp_export import (
    _make_http_session,
    get_cdp_url,
    get_proxy,
    get_site_url,
)

# --create-key / auto-create 状态
_create_key_requested = False
_create_key_name = "auto"
_auto_create_key: bool | None = None  # None=按 config 决定


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _print_chrome_hint() -> None:
    logger.info("\n请确保 Chrome 已启动:")
    logger.info('  open -a "Google Chrome" --args \\')
    logger.info('    --remote-debugging-port=9222 \\')
    logger.info('    --proxy-server="http://127.0.0.1:7890" \\')
    logger.info('    --user-data-dir=/tmp/chrome-cdp')


def read_user_info(cdp_url: str = "") -> dict:
    cdp_url = cdp_url or get_cdp_url()
    proxy = get_proxy()

    logger.info(f"{_ts()} 连接 Chrome (CDP: {cdp_url})...")
    try:
        with CDPSession(cdp_url) as session:
            page = session.page
            result: dict[str, Any] = {
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "cdp_url": cdp_url,
            }

            # 导航到平台页面
            site_url = get_site_url()
            logger.info(f"{_ts()} 导航到 {site_url}...")
            try:
                page.goto(f"{site_url}/platform", wait_until="domcontentloaded", timeout=15000)
            except Exception:
                pass

            current_url = page.url
            logger.info(f"{_ts()} 当前页面: {current_url}")
            result["page_url"] = current_url

            if "login" in current_url:
                logger.info(f"\n{_ts()} 当前未登录，请在 Chrome 中登录后重试。")
                sys.exit(1)

            if "waitlist" in current_url:
                logger.info(f"{_ts()} 账号在 waitlist 中。")

            # 提取 cookies，创建 HTTP session
            cookies = _extract_cookies(page)
            session_http = _make_http_session(cookies, proxy)
            result["zenmux_cookies"] = {k: v[:40] + "..." if len(v) > 40 else v for k, v in cookies.items()}

            # 读取用户信息
            logger.info(f"{_ts()} 读取用户信息...")
            user_info = _read_user_info(page, session_http)
            if user_info:
                result["user_info"] = user_info
                logger.info(f"  userId: {user_info.get('userId', '?')}")
                logger.info(f"  email:  {user_info.get('email', '?')}")
                logger.info(f"  needVerify: {user_info.get('needVerify', '?')}")
            else:
                logger.info("  ⚠ 未能获取用户信息（会话可能未登录）")

            # 读取 API Keys（若不存在则创建）
            logger.info(f"{_ts()} 读取 API Keys...")
            api_keys = _read_api_keys(page, session_http)
            if not api_keys and (_create_key_requested or _should_auto_create_key(_auto_create_key)):
                logger.info(f"{_ts()} 未找到 API Key，尝试创建...")
                new_key = create_api_key(page, session_http, _create_key_name)
                if new_key:
                    api_keys = [new_key]
            result["api_keys"] = api_keys
            if api_keys:
                logger.info(f"  共 {len(api_keys)} 个 API Key:")
                for k in api_keys:
                    name = k.get("name", "?")
                    token = k.get("token", k.get("key", "?"))
                    masked = str(token)[:16] + "..." if len(str(token)) > 20 else token
                    logger.info(f"    - {name}: {masked}")
            else:
                logger.info("  未找到 API Key（可能未登录或未创建")

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

    except ZMError as e:
        logger.info(f"{_ts()} 连接失败: {e.message}")
        if e.hint:
            logger.info(f"Hint: {e.hint}")
        _print_chrome_hint()
        sys.exit(1)
    except Exception as e:
        logger.info(f"{_ts()} 连接失败: {e}")
        _print_chrome_hint()
        sys.exit(1)

    return result


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
    logger.info(f"{_ts()} 结果已保存: {out_path}")

    # 导出 sub2api 格式
    if args.export_sub2api:
        export_sub2api(result, args.export_sub2api_output)

    # 美化打印
    if args.pretty:
        logger.info("\n" + "=" * 60)
        logger.info(json.dumps(result, ensure_ascii=False, indent=2))
