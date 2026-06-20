"""account-status 子命令 handler."""
from __future__ import annotations


def main(cdp_url: str = "") -> None:
    from zm_auto.services.account_status import main as _main
    _main(cdp_url=cdp_url)
