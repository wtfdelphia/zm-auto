"""Captcha constants and base interface."""
from __future__ import annotations

from typing import Protocol


class CaptchaSolverProtocol(Protocol):
    def solve_turnstile(self, page_url: str, timeout: int = 120) -> str:
        ...

    def solve_recaptcha(self, page_url: str, timeout: int = 180, cookies: list[dict] | None = None) -> str:
        ...
