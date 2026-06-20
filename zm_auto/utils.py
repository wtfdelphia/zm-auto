"""JSON utility helpers."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_or_create_json(path: Path, default: Any) -> Any:
    """Load JSON file or create it with default content."""
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default


def _get_dotted(record: dict[str, Any], key: str) -> str:
    obj: Any = record
    for part in key.split("."):
        if not isinstance(obj, dict):
            return ""
        obj = obj.get(part)
    return str(obj) if obj is not None else ""


def append_json_records(
    out_path: Path,
    new_records: list[dict[str, Any]],
    *,
    dedupe_key: str = "credentials.api_key",
) -> None:
    """Append records to a sub2api-compatible export file."""
    existing: list[dict[str, Any]] = []
    if out_path.exists():
        try:
            loaded = json.loads(out_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and "accounts" in loaded:
                existing = loaded.get("accounts", [])
            elif isinstance(loaded, list):
                existing = loaded
        except Exception:
            existing = []

    if not isinstance(existing, list):
        existing = []

    existing_keys = {_get_dotted(a, dedupe_key) for a in existing}
    to_add = [r for r in new_records if _get_dotted(r, dedupe_key) not in existing_keys]
    existing.extend(to_add)

    export_data = {
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "proxies": [],
        "accounts": existing,
    }
    out_path.write_text(json.dumps(export_data, ensure_ascii=False, indent=2), encoding="utf-8")
