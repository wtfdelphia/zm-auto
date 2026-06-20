"""Tests for structured errors and retry utilities."""
from __future__ import annotations

from zm_auto.errors import RetryExhaustedError, RetryableError, RetryPolicy, with_retry, ZmAutoError


class MyRetryableError(RetryableError):
    pass


class OtherError(Exception):
    pass


def test_zm_auto_error_message_and_hint() -> None:
    err = ZmAutoError("missing api key", hint="set captcha.api_key")
    assert str(err) == "missing api key"
    assert err.hint == "set captcha.api_key"


def test_with_retry_returns_immediately() -> None:
    @with_retry
    def func() -> str:
        return "ok"

    assert func() == "ok"


def test_with_retry_retries_then_succeeds() -> None:
    calls = {"count": 0}

    @with_retry
    def func() -> str:
        calls["count"] += 1
        if calls["count"] < 3:
            raise MyRetryableError("temp fail")
        return "ok"

    assert func() == "ok"
    assert calls["count"] == 3


def test_with_retry_exhausts_then_raises() -> None:
    @with_retry
    def func() -> None:
        raise MyRetryableError("always fails")

    try:
        func()
    except RetryExhaustedError as exc:
        assert "always fails" in str(exc)
        assert exc.last_exception is not None
    else:
        raise AssertionError("expected RetryExhaustedError")


def test_with_retry_policy_limits_attempts(monkeypatch: object) -> None:
    sleeps: list[float] = []
    import time
    original_sleep = time.sleep
    time.sleep = sleeps.append  # type: ignore[assignment]

    policy = RetryPolicy(max_retries=2, base_delay=0.1, max_delay=1.0, backoff=1.0)

    @with_retry(policy=policy)
    def func() -> None:
        raise MyRetryableError("fail")

    try:
        func()
    except RetryExhaustedError:
        pass
    finally:
        time.sleep = original_sleep  # type: ignore[assignment]

    assert len(sleeps) == 2


def test_with_retry_does_not_catch_unrelated_exceptions() -> None:
    @with_retry
    def func() -> None:
        raise OtherError("not retryable")

    try:
        func()
    except OtherError:
        pass
    else:
        raise AssertionError("expected OtherError to propagate")
