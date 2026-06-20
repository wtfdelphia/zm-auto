from __future__ import annotations

import sys

from zm_auto.cli import cli

if __name__ == "__main__":
    cli(["user-info", *sys.argv[1:]])
