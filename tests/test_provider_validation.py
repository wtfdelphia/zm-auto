"""Tests for mail provider config validation."""
from __future__ import annotations

import pytest

from zm_auto.providers.base import BaseMailProvider


class _DummyProvider(BaseMailProvider):
    type = "dummy"
    required_fields = ["api_key", "api_secret"]

    def create_mailbox(self, username: str | None = None) -> dict:
        return {"email": "a@b.com"}

    def fetch_latest_message(self, mailbox: dict) -> dict | None:
        return None


class TestValidateConfig:
    def test_valid_config_passes(self) -> None:
        _DummyProvider.validate_config({"api_key": "k", "api_secret": "s"})

    def test_missing_required_field_raises(self) -> None:
        with pytest.raises(ValueError, match="api_key"):
            _DummyProvider.validate_config({"api_secret": "s"})

    def test_empty_required_field_raises(self) -> None:
        with pytest.raises(ValueError, match="api_key"):
            _DummyProvider.validate_config({"api_key": "", "api_secret": "s"})
