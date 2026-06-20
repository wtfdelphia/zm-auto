"""Tests for CDPSession recording helpers."""
from __future__ import annotations

from unittest.mock import MagicMock

from zm_auto.cdp.session import CDPSession


class FakeRequest:
    def __init__(self, method: str = "GET", url: str = "https://example.com/") -> None:
        self.method = method
        self.url = url


class FakeResponse:
    def __init__(self, status: int = 200, url: str = "https://example.com/") -> None:
        self.status = status
        self.url = url
        self.request = FakeRequest("GET", url)


def test_recording_can_be_enabled_and_events_are_captured() -> None:
    session = CDPSession("http://127.0.0.1:9222")
    session._recording_enabled = True

    page = MagicMock()
    handlers: dict[str, object] = {}
    page.on = lambda event, callback: handlers.update({event: callback})
    session._attach_recording(page)

    handlers["request"](FakeRequest("POST", "https://example.com/api"))
    handlers["response"](FakeResponse(201, "https://example.com/api"))

    recording = session.get_recording()
    assert len(recording) == 2
    assert recording[0]["method"] == "POST"
    assert recording[0]["type"] == "request"
    assert recording[1]["type"] == "response"
    assert recording[1]["status"] == 201


def test_clear_recording_empties_buffer() -> None:
    session = CDPSession()
    session._recording_enabled = True
    page = MagicMock()
    handlers: dict[str, object] = {}
    page.on = lambda event, callback: handlers.update({event: callback})
    session._attach_recording(page)

    handlers["request"](FakeRequest())
    assert len(session.get_recording()) == 1
    session.clear_recording()
    assert session.get_recording() == []


def test_recording_disabled_by_default() -> None:
    session = CDPSession()
    assert session.get_recording() == []
