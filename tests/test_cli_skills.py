"""Tests for the skills CLI command."""
from __future__ import annotations

import json

from click.testing import CliRunner

from zm_auto.cli import cli


def _invoke_skills(args: list[str]) -> tuple[int, str]:
    runner = CliRunner()
    result = runner.invoke(cli, ["skills"] + args)
    return result.exit_code, result.output


def test_skills_json_output() -> None:
    exit_code, output = _invoke_skills(["--format", "json"])
    assert exit_code == 0, output
    data = json.loads(output)
    assert "register" in data
    assert "user-info" in data
    assert "doctor" in data
    assert "skills" in data
    assert data["register"]["properties"]["yes"]["type"] == "boolean"


def test_skills_compact_output() -> None:
    exit_code, output = _invoke_skills(["--format", "compact"])
    assert exit_code == 0, output
    data = json.loads(output)
    assert "register" in data
