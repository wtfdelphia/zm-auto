"""Tab management for CDPSession.

借鉴 bb-browser 的 tab 短 ID 设计：每个 tab 有独立生命周期和事件隔离。
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any

from zm_auto.cdp.recording import RecordingBuffer


@dataclass
class Tab:
    """Represents a single browser tab."""

    tab_id: str
    page: Any
    recording: RecordingBuffer = field(default_factory=RecordingBuffer)


def generate_short_id(length: int = 4) -> str:
    """Generate a short hex id like bb-browser's tab short IDs."""
    return secrets.token_hex(length // 2 + length % 2)[:length].lower()
