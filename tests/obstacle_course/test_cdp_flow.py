"""Obstacle course: CDP-related utilities without a real browser."""
from __future__ import annotations

import urllib.request


def test_fixtures_server_user_info(fixtures_server: str) -> None:
    """Verify the fixtures server returns user info."""
    resp = urllib.request.urlopen(f"{fixtures_server}/api/user/info")
    assert resp.status == 200
    data = resp.read().decode("utf-8")
    assert "test@example.com" in data
