"""Tests for enhanced CDP recording."""
from __future__ import annotations

from zm_auto.cdp.recording import RecordingBuffer


def test_recording_seq_increments() -> None:
    buf = RecordingBuffer()
    buf.add_request("GET", "https://example.com/")
    buf.add_response("GET", "https://example.com/", 200)
    entries = buf.get_entries()
    assert entries[0].seq == 1
    assert entries[1].seq == 2


def test_request_response_pairing() -> None:
    buf = RecordingBuffer()
    request_id = buf.add_request("POST", "https://example.com/api")
    buf.add_response("POST", "https://example.com/api", 201, request_id=request_id)
    request, response = buf.get_entries()
    assert request.request_id == response.request_id
    assert response.status == 201


def test_trigger_sets_trigger_seq() -> None:
    buf = RecordingBuffer()
    trigger_seq = buf.mark_trigger("click_submit")
    buf.add_request("GET", "https://example.com/")
    request = buf.get_entries()[1]
    assert request.trigger_seq == trigger_seq


def test_clear_keeps_seq() -> None:
    buf = RecordingBuffer()
    buf.add_request("GET", "https://example.com/")
    buf.clear()
    assert len(buf.get_entries()) == 0
    buf.add_request("GET", "https://example.com/")
    assert buf.get_entries()[0].seq == 2
