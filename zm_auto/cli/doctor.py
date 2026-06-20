"""doctor 子命令 handler.

借鉴 browser-act `get-skills` 的设计思想：输出对 AI Agent 友好的环境状态，
支持结构化的 text 和 JSON 两种格式，便于 Agent 在调用前快速了解当前能力。
"""
from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import click

from zm_auto.config import CONFIG_FILE
from zm_auto.providers import BaseMailProvider


def _cdp_reachable(cdp_url: str) -> bool:
    import urllib.request

    try:
        urllib.request.urlopen(cdp_url, timeout=2)
        return True
    except Exception:
        return False


def _dependency_versions() -> dict[str, str]:
    names = ["pydantic", "click", "curl_cffi", "requests", "urllib3"]
    versions: dict[str, str] = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except Exception:
            versions[name] = "unknown"
    return versions


def _collect_status(format: str) -> dict[str, Any]:
    from zm_auto import __version__
    from zm_auto.config import load_config

    status: dict[str, Any] = {
        "project": "zm-auto",
        "version": __version__,
        "config_file": str(CONFIG_FILE),
    }

    try:
        cfg = load_config()
        status["config"] = {
            "loaded": True,
            "site_url": cfg.site_url,
            "proxy": cfg.proxy or None,
            "captcha_provider": cfg.captcha.provider,
            "cdp_url": cfg.captcha.browser.cdp_url,
            "auto_create_api_key": cfg.auto_create_api_key,
        }
    except Exception as exc:
        status["config"] = {"loaded": False, "error": str(exc)}

    providers = BaseMailProvider.__subclasses__()
    status["mail_providers"] = [
        {
            "type": getattr(p, "type", p.__name__),
            "required_fields": getattr(p, "required_fields", []),
        }
        for p in providers
    ]

    status["captcha_providers"] = [
        {"name": "2captcha", "layer": "paid_api", "requires_api_key": True},
        {"name": "anticaptcha", "layer": "paid_api", "requires_api_key": True},
        {"name": "browser", "layer": "execution", "requires_api_key": False},
        {"name": "cdp", "layer": "human", "requires_api_key": False},
    ]

    cdp_url = "http://127.0.0.1:9222"
    config = status.get("config")
    if isinstance(config, dict) and "cdp_url" in config:
        cdp_url = config["cdp_url"]
    cdp_reachable = _cdp_reachable(cdp_url)
    status["cdp_reachable"] = cdp_reachable

    # Overall health: config loaded + CDP reachable + all key deps present.
    deps = _dependency_versions()
    config_loaded = isinstance(config, dict) and config.get("loaded") is True
    status["ok"] = config_loaded and cdp_reachable and all(v != "unknown" for v in deps.values())

    status["output_files"] = {
        "accounts": str(Path(CONFIG_FILE).with_name("accounts.json")),
        "user_info": str(Path(CONFIG_FILE).with_name("user_info.json")),
        "sub2api_export": str(Path(CONFIG_FILE).with_name("sub2api_export.json")),
    }
    status["dependencies"] = deps
    return status


def _format_text(status: dict[str, Any]) -> str:
    lines = ["zm-auto doctor", "=" * 60]
    lines.append(f"project: {status['project']}")
    lines.append(f"version: {status['version']}")
    lines.append(f"config file: {status['config_file']}")

    config = status.get("config")
    if isinstance(config, dict):
        if config.get("loaded"):
            lines.append("config loaded: ok")
            lines.append(f"  site_url: {config.get('site_url')}")
            lines.append(f"  proxy: {config.get('proxy') or '无'}")
            lines.append(f"  captcha_provider: {config.get('captcha_provider')}")
            lines.append(f"  auto_create_api_key: {config.get('auto_create_api_key')}")
        else:
            lines.append(f"config loaded: failed - {config.get('error')}")

    lines.append("mail providers:")
    for p in status.get("mail_providers", []):
        req = ", ".join(p.get("required_fields", []) or ["无"])
        lines.append(f"  - {p['type']} (required: {req})")

    lines.append("captcha providers:")
    for p in status.get("captcha_providers", []):
        lines.append(f"  - {p['name']} [{p['layer']}] requires_api_key={p['requires_api_key']}")

    reachable = status.get("cdp_reachable")
    lines.append(f"cdp reachable: {'yes' if reachable else 'no (Chrome may not be running)'}")
    return "\n".join(lines)


def _format_compact(status: dict[str, Any]) -> str:
    config = status.get("config", {})
    loaded = "ok" if isinstance(config, dict) and config.get("loaded") else "err"
    providers = ",".join(p["type"] for p in status.get("mail_providers", []))
    cdp = "yes" if status.get("cdp_reachable") else "no"
    deps = status.get("dependencies", {})
    deps_str = ",".join(f"{k}={v}" for k, v in deps.items())
    return (
        f"project={status['project']} version={status['version']} "
        f"config={loaded} providers={providers} cdp={cdp} deps={deps_str}"
    )


def main(format: str = "text", compact: bool = False) -> None:
    if format not in ("text", "json"):
        raise click.UsageError("--format 必须是 text 或 json")
    if compact and format != "json":
        format = "compact"

    status = _collect_status(format)
    if format == "json":
        click.echo(json.dumps(status, ensure_ascii=False, indent=2))
    elif format == "compact":
        click.echo(_format_compact(status))
    else:
        click.echo(_format_text(status))
