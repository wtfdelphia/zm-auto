"""Regression tests for legacy root-level CLI entry points."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from zm_auto.cli import cli


ROOT = Path(__file__).parent.parent


def _run_script(script_name: str, args: list[str]) -> tuple[int, str, str]:
    script = ROOT / script_name
    result = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def test_register_py_help_shows_register_help() -> None:
    returncode, stdout, _ = _run_script("register.py", ["--help"])
    assert returncode == 0
    assert "Usage: register.py register [OPTIONS]" in stdout
    assert "-n INTEGER" in stdout or "--total" in stdout


def test_read_user_info_py_help_shows_user_info_help() -> None:
    returncode, stdout, _ = _run_script("read_user_info.py", ["--help"])
    assert returncode == 0
    assert "Usage: read_user_info.py user-info [OPTIONS]" in stdout
    assert "--cdp-url" in stdout


def test_check_account_status_py_help_shows_account_status_help() -> None:
    returncode, stdout, _ = _run_script("check_account_status.py", ["--help"])
    assert returncode == 0
    assert "Usage: check_account_status.py account-status [OPTIONS]" in stdout
    assert "--cdp-url" in stdout


def test_account_status_cdp_url_passed_to_service() -> None:
    """`account-status --cdp-url <url>` should forward the URL to the service layer."""
    captured: dict[str, str] = {}

    def fake_main(cdp_url: str = "") -> None:
        captured["cdp_url"] = cdp_url

    with mock.patch("zm_auto.services.account_status.main", fake_main):
        runner = CliRunner()
        result = runner.invoke(cli, ["account-status", "--cdp-url", "http://test-cdp:9222"])

    assert result.exit_code == 0, result.output
    assert captured.get("cdp_url") == "http://test-cdp:9222"
