"""Tests for doctor CLI output."""
from __future__ import annotations

import json

from click.testing import CliRunner

from zm_auto.cli import cli


def _invoke_doctor(args: list[str]) -> tuple[int, str]:
    runner = CliRunner()
    result = runner.invoke(cli, ["doctor"] + args)
    return result.exit_code, result.output


def test_doctor_json_output() -> None:
    exit_code, output = _invoke_doctor(["--format", "json"])
    assert exit_code == 0, output
    data = json.loads(output)
    assert "dependencies" in data
    assert "mail_providers" in data
    assert "captcha_providers" in data
    assert "cdp_reachable" in data
    assert "ok" in data
    assert isinstance(data["ok"], bool)


def test_doctor_default_text_output() -> None:
    exit_code, output = _invoke_doctor([])
    assert exit_code == 0, output
    assert "zm-auto doctor" in output


def test_doctor_compact_output() -> None:
    exit_code, output = _invoke_doctor(["--compact"])
    assert exit_code == 0, output
    assert "project=" in output
