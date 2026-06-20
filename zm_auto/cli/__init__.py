"""Click CLI entry point."""
from __future__ import annotations

import importlib
from typing import Any

import click

from zm_auto.cli.commands import COMMANDS, CommandDef
from zm_auto.exceptions import ZMError
from zm_auto.logging_config import setup_logging


_TYPE_MAP: dict[str, click.ParamType] = {
    "string": click.STRING,
    "number": click.INT,
    "boolean": click.BOOL,
}


def _make_command(cmd: CommandDef) -> click.Command:
    def _invoke(**kwargs: Any) -> Any:
        module_name, func_name = cmd.handler.split(":")
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)
        return func(**kwargs)

    params: list[click.Parameter] = []
    for p in cmd.params:
        decls = [p.option_name]
        if p.flag and p.flag != p.option_name:
            decls.insert(0, p.flag)
        click_type = _TYPE_MAP.get(p.type, click.STRING)
        if p.is_flag:
            params.append(
                click.Option(decls, default=p.default or False, is_flag=True, help=p.help, show_default=False)
            )
        else:
            show = p.default is not None
            params.append(
                click.Option(decls, type=click_type, default=p.default, help=p.help, show_default=show)
            )

    return click.Command(name=cmd.name, callback=_invoke, help=cmd.description, params=params)


@click.group()
@click.option("--verbose", is_flag=True, help="启用 DEBUG 级别日志")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """zm-auto 命令行入口。"""
    setup_logging(verbose)
    ctx.ensure_object(dict)


def _register_commands() -> None:
    for cmd in COMMANDS:
        cli.add_command(_make_command(cmd))


_register_commands()


def main() -> None:
    try:
        cli()
    except ZMError as e:
        click.echo(f"Error: {e.message}", err=True)
        if e.hint:
            click.echo(f"Hint: {e.hint}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
