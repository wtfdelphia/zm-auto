from __future__ import annotations

import sys

from zm_auto.cli import cli

if __name__ == "__main__":
    cli(["account-status", *sys.argv[1:]])
