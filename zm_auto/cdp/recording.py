"""Recording data structures for CDPSession.

借鉴 bb-browser trace timeline 的设计思想：为每个网络事件分配单调 seq、
request/response 配对、trigger 因果链，方便离线调试。
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RecordingEntry:
    """Base class for a recording entry."""

    seq: int
    timestamp: float
    type: str = "entry"
    trigger_seq: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "timestamp": self.timestamp,
            "type": self.type,
            "trigger_seq": self.trigger_seq,
        }


@dataclass
class RequestEntry(RecordingEntry):
    """A network request recording entry."""

    method: str = "GET"
    url: str = ""
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "type": "request",
            "method": self.method,
            "url": self.url,
            "request_id": self.request_id,
        })
        return base


@dataclass
class ResponseEntry(RecordingEntry):
    """A network response recording entry."""

    method: str = "GET"
    url: str = ""
    status: int = 0
    request_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "type": "response",
            "method": self.method,
            "url": self.url,
            "status": self.status,
            "request_id": self.request_id,
        })
        return base


@dataclass
class TriggerEntry(RecordingEntry):
    """A trigger marker in the recording."""

    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "type": "trigger",
            "name": self.name,
        })
        return base


class RecordingBuffer:
    """Buffer for recording network events with seq and trigger tracking."""

    def __init__(self) -> None:
        self._entries: list[RecordingEntry] = []
        self._seq = 0
        self._last_trigger_seq: int | None = None

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def add_request(self, method: str, url: str) -> str:
        """Add a request entry and return its request_id."""
        request_id = uuid.uuid4().hex
        entry = RequestEntry(
            seq=self._next_seq(),
            timestamp=time.time(),
            method=method,
            url=url,
            request_id=request_id,
            trigger_seq=self._last_trigger_seq,
        )
        self._entries.append(entry)
        return request_id

    def add_response(self, method: str, url: str, status: int, request_id: str = "") -> None:
        self._entries.append(
            ResponseEntry(
                seq=self._next_seq(),
                timestamp=time.time(),
                method=method,
                url=url,
                status=status,
                request_id=request_id,
                trigger_seq=self._last_trigger_seq,
            )
        )

    def mark_trigger(self, name: str) -> int:
        seq = self._next_seq()
        self._entries.append(
            TriggerEntry(
                seq=seq,
                timestamp=time.time(),
                name=name,
            )
        )
        self._last_trigger_seq = seq
        return seq

    def get_entries(self) -> list[RecordingEntry]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        # Keep seq monotonic across the session; do not reset _seq.

    def to_dicts(self) -> list[dict[str, Any]]:
        return [entry.to_dict() for entry in self._entries]
