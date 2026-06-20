"""Structured errors and retry utilities.

借鉴 obscura 的健壮性设计：统一业务错误表示，对可重试错误提供
最大次数、指数退避、最大延迟等策略，减少临时网络/页面波动导致的偶发失败。
"""
from __future__ import annotations

import functools
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, TypeVar


class ZmAutoError(Exception):
    """Base exception for zm-auto business errors."""

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self) -> str:
        return self.message


class RetryableError(ZmAutoError):
    """Exception that can be retried by ``with_retry``."""


class RetryExhaustedError(ZmAutoError):
    """Raised when retries are exhausted."""

    def __init__(self, message: str, last_exception: Exception | None = None, hint: str = "") -> None:
        super().__init__(message, hint=hint)
        self.last_exception = last_exception


@dataclass
class RetryPolicy:
    """Retry policy configuration."""

    max_retries: int = 3
    base_delay: float = 0.5
    max_delay: float = 30.0
    backoff: float = 2.0
    retryable_exceptions: tuple[type[Exception], ...] = (RetryableError,)

    def compute_delay(self, attempt: int) -> float:
        """Compute delay before the next retry (attempt starts at 0)."""
        delay = self.base_delay * (self.backoff ** attempt)
        return min(delay, self.max_delay)


F = TypeVar("F", bound=Callable[..., Any])


def with_retry(
    func: F | None = None,
    *,
    policy: RetryPolicy | None = None,
    retryable: type[Exception] | Iterable[type[Exception]] | None = None,
) -> F | Callable[[F], F]:
    """Decorator/helper to retry a function according to a RetryPolicy.

    Can be used as a decorator with a policy, or as a function wrapper.
    """
    if policy is None:
        policy = RetryPolicy()
    if retryable is not None:
        if isinstance(retryable, type):
            retryable = (retryable,)
        else:
            retryable = tuple(retryable)
        policy = RetryPolicy(
            max_retries=policy.max_retries,
            base_delay=policy.base_delay,
            max_delay=policy.max_delay,
            backoff=policy.backoff,
            retryable_exceptions=retryable,
        )

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(policy.max_retries + 1):  # pylint: disable=W0631
                try:
                    return func(*args, **kwargs)
                except policy.retryable_exceptions as exc:  # type: ignore[misc]
                    last_exc = exc
                    if attempt >= policy.max_retries:
                        raise RetryExhaustedError(
                            f"重试 {policy.max_retries} 次后仍失败: {exc}",
                            last_exception=exc,
                        ) from exc
                    time.sleep(policy.compute_delay(attempt))
            # Should never reach here
            raise RetryExhaustedError("重试逻辑异常", last_exception=last_exc)

        return wrapper  # type: ignore[return-value]

    if func is None:
        return decorator
    return decorator(func)
