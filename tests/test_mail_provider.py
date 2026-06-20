"""Tests for mail_provider.py pure helper functions (no network calls)."""

import re
from datetime import datetime, timezone

import pytest

from zm_auto.providers import (
    _config,
    _random_mailbox_name,
    _random_subdomain_label,
    _next_domain,
    _parse_received_at,
    _extract_content,
    _extract_text_candidates,
    _message_matches_email,
    _extract_code,
    _message_tracking_ref,
    _entries,
    _enabled_entries,
    _next_entry,
    _create_provider,
    _FORBIDDEN_CODES,
)


# --------------------------------------------------------------------------- #
# _config
# --------------------------------------------------------------------------- #
class TestConfig:
    def test_defaults_all(self):
        result = _config({})
        assert result["request_timeout"] == 30.0
        assert result["wait_timeout"] == 60.0
        assert result["wait_interval"] == 2.0
        assert result["user_agent"] == "Mozilla/5.0"

    def test_custom_values(self):
        result = _config({
            "request_timeout": "10",
            "wait_timeout": "300",
            "wait_interval": "5",
            "user_agent": "MyAgent/1.0",
        })
        assert result["request_timeout"] == 10.0
        assert result["wait_timeout"] == 300.0
        assert result["wait_interval"] == 5.0
        assert result["user_agent"] == "MyAgent/1.0"

    def test_falsy_values_fallback_to_defaults(self):
        result = _config({
            "request_timeout": 0,
            "wait_timeout": "",
            "wait_interval": None,
            "user_agent": "",
        })
        assert result["request_timeout"] == 30.0
        assert result["wait_timeout"] == 60.0
        assert result["wait_interval"] == 2.0
        assert result["user_agent"] == "Mozilla/5.0"


# --------------------------------------------------------------------------- #
# _random_mailbox_name
# --------------------------------------------------------------------------- #
class TestRandomMailboxName:
    def test_returns_nonempty_string(self):
        name = _random_mailbox_name()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_only_lowercase_and_digits(self):
        for _ in range(50):
            name = _random_mailbox_name()
            assert re.fullmatch(r"[a-z0-9]+", name), f"Unexpected chars in: {name}"

    def test_length_between_7_and_11(self):
        """5 letters + 1-3 digits + 1-3 letters = 7-11 chars."""
        for _ in range(50):
            name = _random_mailbox_name()
            assert 7 <= len(name) <= 11, f"Unexpected length: {len(name)} ({name})"


# --------------------------------------------------------------------------- #
# _random_subdomain_label
# --------------------------------------------------------------------------- #
class TestRandomSubdomainLabel:
    def test_returns_nonempty_string(self):
        label = _random_subdomain_label()
        assert isinstance(label, str)
        assert len(label) > 0

    def test_length_between_4_and_10(self):
        for _ in range(50):
            label = _random_subdomain_label()
            assert 4 <= len(label) <= 10, f"Unexpected length: {len(label)}"

    def test_only_alphanumeric(self):
        for _ in range(50):
            label = _random_subdomain_label()
            assert re.fullmatch(r"[a-z0-9]+", label), f"Unexpected chars in: {label}"


# --------------------------------------------------------------------------- #
# _next_domain
# --------------------------------------------------------------------------- #
class TestNextDomain:
    def test_single_domain_returns_it(self):
        assert _next_domain(["example.com"]) == "example.com"

    def test_empty_list_raises(self):
        with pytest.raises(RuntimeError, match="mail.domain"):
            _next_domain([])

    def test_all_empty_strings_raises(self):
        with pytest.raises(RuntimeError, match="mail.domain"):
            _next_domain(["", "  "])

    def test_round_robin(self):
        domains = ["a.com", "b.com", "c.com"]
        results = [_next_domain(domains) for _ in range(6)]
        assert results == ["a.com", "b.com", "c.com", "a.com", "b.com", "c.com"]

    def test_strips_whitespace(self):
        domains = ["  a.com  ", " b.com "]
        assert _next_domain(domains) == "a.com"
        assert _next_domain(domains) == "b.com"


# --------------------------------------------------------------------------- #
# _parse_received_at
# --------------------------------------------------------------------------- #
class TestParseReceivedAt:
    def test_unix_timestamp(self):
        result = _parse_received_at(1700000000.0)
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc
        assert result.year == 2023

    def test_iso_format_z(self):
        result = _parse_received_at("2024-01-15T10:30:00Z")
        assert result == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_iso_format_with_offset(self):
        result = _parse_received_at("2024-01-15T10:30:00+00:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_iso_format_no_tz(self):
        result = _parse_received_at("2024-01-15T10:30:00")
        assert result.tzinfo == timezone.utc

    def test_rfc2822_format(self):
        result = _parse_received_at("Mon, 15 Jan 2024 10:30:00 +0000")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_empty_string_returns_none(self):
        assert _parse_received_at("") is None
        assert _parse_received_at("  ") is None

    def test_none_returns_none(self):
        assert _parse_received_at(None) is None

    def test_invalid_string_returns_none(self):
        assert _parse_received_at("not-a-date") is None


# --------------------------------------------------------------------------- #
# _extract_content
# --------------------------------------------------------------------------- #
class TestExtractContent:
    def test_extracts_text_content(self):
        data = {"text_content": "Hello world"}
        text, html = _extract_content(data)
        assert text == "Hello world"
        assert html == ""

    def test_falls_back_to_text(self):
        data = {"text": "Fallback text"}
        text, html = _extract_content(data)
        assert text == "Fallback text"

    def test_extracts_html_content(self):
        data = {"html_content": "<p>Hi</p>"}
        text, html = _extract_content(data)
        assert text == ""
        assert html == "<p>Hi</p>"

    def test_returns_empty_for_empty_dict(self):
        text, html = _extract_content({})
        assert text == ""
        assert html == ""


# --------------------------------------------------------------------------- #
# _extract_text_candidates
# --------------------------------------------------------------------------- #
class TestExtractTextCandidates:
    def test_string_returns_list(self):
        assert _extract_text_candidates("hello") == ["hello"]

    def test_dict_with_address(self):
        assert _extract_text_candidates({"address": "a@b.com"}) == ["a@b.com"]

    def test_dict_with_email(self):
        assert _extract_text_candidates({"email": "x@y.com"}) == ["x@y.com"]

    def test_dict_with_name(self):
        assert _extract_text_candidates({"name": "Alice"}) == ["Alice"]

    def test_list_of_dicts(self):
        result = _extract_text_candidates([{"address": "a@b.com"}, {"name": "Bob"}])
        assert result == ["a@b.com", "Bob"]

    def test_empty_list(self):
        assert _extract_text_candidates([]) == []

    def test_empty_dict(self):
        assert _extract_text_candidates({}) == []


# --------------------------------------------------------------------------- #
# _message_matches_email
# --------------------------------------------------------------------------- #
class TestMessageMatchesEmail:
    def test_direct_match(self):
        data = {"to": "user@example.com"}
        assert _message_matches_email(data, "user@example.com") is True

    def test_case_insensitive(self):
        data = {"to": "User@Example.COM"}
        assert _message_matches_email(data, "user@example.com") is True

    def test_no_match(self):
        data = {"to": "other@example.com"}
        assert _message_matches_email(data, "user@example.com") is False

    def test_empty_email_returns_true(self):
        data = {"to": "anything@example.com"}
        assert _message_matches_email(data, "") is True

    def test_no_candidates_returns_true(self):
        data = {"subject": "Hello"}
        assert _message_matches_email(data, "user@example.com") is True


# --------------------------------------------------------------------------- #
# _extract_code
# --------------------------------------------------------------------------- #
class TestExtractCode:
    def test_extracts_6_digit_from_subject(self):
        msg = {"subject": "Your verification code is 123456", "text_content": "", "html_content": ""}
        assert _extract_code(msg) == "123456"

    def test_extracts_6_digit_from_text_content(self):
        msg = {"subject": "", "text_content": "Code: 987654 for login", "html_content": ""}
        assert _extract_code(msg) == "987654"

    def test_extracts_styled_code_block(self):
        msg = {
            "subject": "",
            "text_content": "",
            "html_content": '<p style="background-color:#F3F3F3">Your code: 456789</p>',
        }
        assert _extract_code(msg) == "456789"

    def test_extracts_standalone_6_digit(self):
        msg = {"subject": "", "text_content": "Here is 111222 for you", "html_content": ""}
        assert _extract_code(msg) == "111222"

    def test_skips_forbidden_code(self):
        msg = {"subject": "Your code is 177010", "text_content": "", "html_content": ""}
        # 177010 is in _FORBIDDEN_CODES, should be skipped
        result = _extract_code(msg)
        assert result is None or result != "177010"

    def test_empty_content_returns_none(self):
        msg = {"subject": "", "text_content": "", "html_content": ""}
        assert _extract_code(msg) is None

    def test_chinese_verification_code(self):
        msg = {"subject": "验证码：123456", "text_content": "", "html_content": ""}
        assert _extract_code(msg) == "123456"


# --------------------------------------------------------------------------- #
# _message_tracking_ref
# --------------------------------------------------------------------------- #
class TestMessageTrackingRef:
    def test_with_message_id(self):
        msg = {"provider": "gptmail", "mailbox": "test@test.com", "message_id": "msg-123"}
        ref = _message_tracking_ref(msg)
        assert ref.startswith("id:")
        assert "gptmail" in ref
        assert "test@test.com" in ref
        assert "msg-123" in ref

    def test_without_message_id(self):
        msg = {
            "provider": "gptmail",
            "mailbox": "test@test.com",
            "message_id": "",
            "received_at": None,
            "subject": "Hello",
            "sender": "noreply",
            "text_content": "",
            "html_content": "",
        }
        ref = _message_tracking_ref(msg)
        assert ref.startswith("content:")
        assert "gptmail" in ref
        assert len(ref) > 50  # includes sha256 digest


# --------------------------------------------------------------------------- #
# _entries / _enabled_entries / _next_entry
# --------------------------------------------------------------------------- #
class TestEntries:
    def test_entries_returns_list(self):
        result = _entries({"providers": [{"type": "gptmail", "api_key": "k"}]})
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "gptmail"
        assert "provider_ref" in result[0]

    def test_enabled_entries_filters_disabled(self):
        """_enabled_entries only includes entries with truthy 'enable' key."""
        cfg = {
            "providers": [
                {"type": "gptmail", "enable": True},
                {"type": "tempmail_lol", "enable": False},
                {"type": "duckmail", "enable": True},
            ]
        }
        result = _enabled_entries(cfg)
        assert len(result) == 2
        types = [e["type"] for e in result]
        assert "gptmail" in types
        assert "duckmail" in types
        assert "tempmail_lol" not in types

    def test_enabled_entries_no_enable_key_excluded(self):
        """Entries without 'enable' key are excluded (item.get('enable') returns None)."""
        cfg = {
            "providers": [
                {"type": "gptmail", "enable": True},
                {"type": "duckmail"},  # no enable key → excluded
            ]
        }
        result = _enabled_entries(cfg)
        assert len(result) == 1
        assert result[0]["type"] == "gptmail"

    def test_next_entry_round_robin(self):
        cfg = {
            "providers": [
                {"type": "a", "enable": True},
                {"type": "b", "enable": True},
            ]
        }
        e1 = _next_entry(cfg)
        e2 = _next_entry(cfg)
        e3 = _next_entry(cfg)
        assert e1["type"] == "a"
        assert e2["type"] == "b"
        assert e3["type"] == "a"

    def test_next_entry_no_enabled_raises(self):
        cfg = {"providers": [{"type": "a", "enable": False}]}
        with pytest.raises(RuntimeError, match="没有启用的 provider"):
            _next_entry(cfg)


# --------------------------------------------------------------------------- #
# _create_provider
# --------------------------------------------------------------------------- #
class TestCreateProvider:
    def test_creates_gptmail_provider(self):
        provider = _create_provider(
            {"providers": [{"type": "gptmail", "api_key": "key123", "enable": True}]},
            provider="gptmail",
        )
        assert provider.name == "gptmail"

    def test_unknown_provider_raises(self):
        with pytest.raises(RuntimeError, match="不支持的 mail.provider"):
            _create_provider(
                {"providers": [{"type": "nonexistent", "enable": True}]},
                provider="nonexistent",
            )

    def test_uses_provider_ref(self):
        provider = _create_provider(
            {"providers": [{"type": "gptmail", "api_key": "key123", "enable": True}]},
            provider="",
            provider_ref="gptmail#1",
        )
        assert provider.name == "gptmail"


# --------------------------------------------------------------------------- #
# _FORBIDDEN_CODES
# --------------------------------------------------------------------------- #
class TestForbiddenCodes:
    def test_contains_177010(self):
        assert "177010" in _FORBIDDEN_CODES
