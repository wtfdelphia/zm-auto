"""Captcha login solver entry point."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import sys

from zm_auto.captcha.cdp import CDPRecaptchaSolver, CDPTurnstileSolver
from zm_auto.captcha.login_solver import CDPLoginSolver
from zm_auto.config import load_config


def _load_site_url() -> str:
    try:
        return str(load_config().site_url).rstrip("/")
    except Exception:
        return "https://example.com"


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
        recaptcha_solver = CDPRecaptchaSolver()
        try:
            token = recaptcha_solver.solve(url)
            logger.info(f"\nToken: {token}")
        except Exception as e:
            logger.info(f"\n失败: {e}{hint}")

    elif mode == "login":
        url = url or f"{_load_site_url()}/login"
        email = sys.argv[3] if len(sys.argv) > 3 else ""
        if not email:
            logger.info("用法: python cdp_solver.py login <url> <email>")
            sys.exit(1)

        def dummy_get_code() -> str | None:
            return input("请输入邮箱验证码: ").strip() or None

        login_solver = CDPLoginSolver()
        try:
            result = login_solver.login(url, email, dummy_get_code)
            cookies = result.get("cookies", [])
            logger.info(f"\nCookies: {len(cookies)} 个")
            for c in cookies:
                logger.info(f"  {c['name']}={c['value'][:20]}...")
        except Exception as e:
            logger.info(f"\n失败: {e}{hint}")

    else:
        url = url or f"{_load_site_url()}/login"
        turnstile_solver = CDPTurnstileSolver()
        try:
            token = turnstile_solver.solve(url)
            logger.info(f"\nToken: {token}")
        except Exception as e:
            logger.info(f"\n失败: {e}{hint}")
