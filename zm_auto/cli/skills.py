"""skills 子命令：导出 AI Agent 可用的 CLI skill schema.

借鉴 browser-act `get-skills` 的设计思想：让 Agent 在调用前先获取命令签名。
"""
from __future__ import annotations

import json

import click

from zm_auto.cli.commands import registry_json_schema


def main(format: str = "json") -> None:
    if format == "compact":
        schema = registry_json_schema()
        click.echo(json.dumps(schema, ensure_ascii=False, separators=(",", ":")))
    else:
        schema = registry_json_schema()
        click.echo(json.dumps(schema, ensure_ascii=False, indent=2))
