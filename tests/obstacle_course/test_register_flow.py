"""Obstacle course: register flow against local fixtures."""
from __future__ import annotations

import urllib.request


def test_send_code_endpoint(fixtures_server: str) -> None:
    """Verify the local send-code endpoint works."""
    import json
    req = urllib.request.Request(
        f"{fixtures_server}/api/auth/email/send-code",
        data=b"",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    assert resp.status == 200
    data = json.loads(resp.read().decode("utf-8"))
    assert data["ok"] is True
    assert "code" in data
