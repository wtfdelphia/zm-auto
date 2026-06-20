""""register 子命令 handler."""
from __future__ import annotations

import click

from zm_auto.config import load_config



def main(total: int | None = None, threads: int | None = None, proxy: str = "", yes: bool = False) -> None:
    cfg = load_config().model_dump()
    # Sensitive operations confirmation
    if not yes:
        provider = cfg["captcha"]["provider"]
        if provider in ("2captcha", "anticaptcha", "cdp") or cfg["auto_create_api_key"]:
            click.confirm("该操作可能产生费用或调用付费服务，是否继续?", abort=True)

    from zm_auto.services.registrar import config as reg_config
    from zm_auto.services.registrar import run
    if total is not None:
        reg_config["total"] = total
    if threads is not None:
        reg_config["threads"] = threads
    if proxy:
        reg_config["proxy"] = proxy
    run(total=reg_config["total"], threads=reg_config["threads"])
