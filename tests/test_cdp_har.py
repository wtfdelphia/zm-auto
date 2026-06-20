"""Tests for CDP HAR export."""
from __future__ import annotations

import json

from zm_auto.cdp.har import build_har
from zm_auto.cdp.session import CDPSession


def test_empty_recording_yields_empty_har() -> None:
    har = build_har([])
    assert har["log"]["version"] == "1.2"
    assert har["log"]["creator"]["name"] == "zm-auto"
    assert har["log"]["entries"] == []


def test_single_request_entry() -> None:
    har = build_har([
        {"type": "request", "timestamp": 1700000000.0, "method": "GET", "url": "https://example.com/"},
    ])
    assert len(har["log"]["entries"]) == 1
    entry = har["log"]["entries"][0]
    assert entry["request"]["method"] == "GET"
    assert entry["request"]["url"] == "https://example.com/"
    assert entry["startedDateTime"].endswith("Z")


def test_response_entry_has_status() -> None:
    har = build_har([
        {"type": "response", "timestamp": 1700000000.0, "method": "POST", "url": "https://example.com/api", "status": 201},
    ])
    entry = har["log"]["entries"][0]
    assert entry["response"]["status"] == 201
    assert entry["request"]["method"] == "POST"


def test_har_json_roundtrip() -> None:
    har = build_har([
        {"type": "response", "timestamp": 1700000000.0, "method": "GET", "url": "https://example.com/", "status": 200},
    ])
    dumped = json.dumps(har)
    loaded = json.loads(dumped)
    assert loaded["log"]["entries"][0]["response"]["status"] == 200


def test_cdp_session_export_har() -> None:
    session = CDPSession()
    # Create a mock tab/recording manually without opening a browser.
    from zm_auto.cdp.tab import Tab
    from zm_auto.cdp.recording import RecordingBuffer
    tab = Tab(tab_id="abcd", page=None, recording=RecordingBuffer())
    session._tabs["abcd"] = tab
    session._active_tab_id = "abcd"
    tab.recording.add_request(method="GET", url="https://example.com/")
    request_id = tab.recording._entries[0].request_id
    tab.recording.add_response(method="GET", url="https://example.com/", status=200, request_id=request_id)
    har = session.export_har()
    assert len(har["log"]["entries"]) == 2
