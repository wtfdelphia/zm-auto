"""Standard error envelope."""
from __future__ import annotations


class ZMError(Exception):
    """Standard zm-auto error with message and hint."""

    def __init__(self, message: str = "", hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint
