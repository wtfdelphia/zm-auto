"""user-info 子命令 handler."""
from __future__ import annotations

from pathlib import Path

import click


def main(
    cdp_url: str = "",
    output: str = "",
    export_sub2api: bool = False,
    export_sub2api_output: str = "",
    pretty: bool = False,
    api_keys_only: bool = False,
    user_only: bool = False,
    create_key: str | None = None,
    yes: bool = False,
) -> None:
    if not yes and (create_key or cdp_url):
        click.confirm("该操作会连接 CDP 或创建 API Key，是否继续?", abort=True)

    from zm_auto.services import user_info as user_info_mod

    if create_key:
        user_info_mod._create_key_requested = True
        user_info_mod._create_key_name = create_key

    result = user_info_mod.read_user_info(cdp_url=cdp_url)

    out_path = Path(output) if output else (user_info_mod.BASE_DIR / "user_info.json")
    import json
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    click.echo(f"结果已保存: {out_path}")

    if export_sub2api:
        user_info_mod.export_sub2api(result, export_sub2api_output)

    if pretty:
        click.echo("\n" + "=" * 60)
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
