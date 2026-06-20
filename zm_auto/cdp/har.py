"""HAR 1.2 export for CDPSession recordings.

借鉴 bb-browser / browser-act 的网络调试能力：
把 CDPSession 内部录制的 request/response 事件导出为标准 HAR JSON，
方便在浏览器开发者工具或第三方工具中离线分析。
"""
from __future__ import annotations

import datetime
from typing import Any


def _iso_time(ts: float) -> str:
    """Convert unix timestamp to HAR/ISO 8601 UTC string."""
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _build_request(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "method": entry.get("method", "GET"),
        "url": entry.get("url", ""),
        "httpVersion": "HTTP/1.1",
        "headers": [],
        "queryString": [],
        "cookies": [],
        "headersSize": -1,
        "bodySize": -1,
    }


def _build_response(entry: dict[str, Any]) -> dict[str, Any]:
    status = entry.get("status")
    try:
        status = int(status) if status is not None else 0
    except (TypeError, ValueError):
        status = 0
    return {
        "status": status,
        "statusText": "",
        "httpVersion": "HTTP/1.1",
        "headers": [],
        "cookies": [],
        "content": {
            "size": -1,
            "mimeType": "",
        },
        "redirectURL": "",
        "headersSize": -1,
        "bodySize": -1,
    }


def _build_entry(entry: dict[str, Any]) -> dict[str, Any]:
    timestamp = entry.get("timestamp")
    try:
        started = float(timestamp) if timestamp is not None else 0.0
    except (TypeError, ValueError):
        started = 0.0
    # HAR time is total time in ms; we do not have real timing, use 0.
    return {
        "startedDateTime": _iso_time(started),
        "time": 0,
        "request": _build_request(entry),
        "response": _build_response(entry),
        "cache": {},
        "timings": {
            "blocked": -1,
            "dns": -1,
            "connect": -1,
            "send": 0,
            "wait": 0,
            "receive": 0,
            "ssl": -1,
        },
    }


def build_har(recording: list[dict[str, Any]], *, title: str = "zm-auto") -> dict[str, Any]:
    """Build a HAR 1.2 object from a CDPSession recording list."""
    entries = [_build_entry(entry) for entry in recording]
    return {
        "log": {
            "version": "1.2",
            "creator": {"name": "zm-auto", "version": "1.0"},
            "title": title,
            "pages": [
                {
                    "id": title,
                    "title": title,
                    "startedDateTime": _iso_time(0.0),
                    "pageTimings": {"onContentLoad": -1, "onLoad": -1},
                }
            ],
            "entries": entries,
        }
    }


def export_har(recording: list[dict[str, Any]], *, title: str = "zm-auto") -> dict[str, Any]:
    """Alias for build_har, kept for naming symmetry with CDPSession.export_har()."""
    return build_har(recording, title=title)
