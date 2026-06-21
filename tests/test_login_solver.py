"""Tests for zm_auto/captcha/login_solver.py (no browser)."""

import time
from unittest.mock import patch

import pytest

from zm_auto.captcha.login_solver import CDPLoginSolver


class FakePage:
    """Minimal page stub for _wait_for_login_or_verify."""

    def __init__(self, url_sequence, evaluate_responses):
        self._url_sequence = list(url_sequence)
        self._evaluate_responses = list(evaluate_responses)
        self._url_index = 0
        self._eval_index = 0

    @property
    def url(self):
        if self._url_index < len(self._url_sequence):
            return self._url_sequence[self._url_index]
        return self._url_sequence[-1]

    def advance_url(self):
        self._url_index += 1

    def evaluate(self, *args, **kwargs):
        if self._eval_index < len(self._evaluate_responses):
            resp = self._evaluate_responses[self._eval_index]
            self._eval_index += 1
            return resp
        return {}


def _run_with_patched_sleep(page, timeout=1, verify_wait=0):
    """Run _wait_for_login_or_verify with patched time.sleep to keep tests fast."""
    with patch("zm_auto.captcha.login_solver.time.sleep"):
        CDPLoginSolver._wait_for_login_or_verify(page, timeout=timeout, verify_wait=verify_wait)


class TestWaitForLoginOrVerify:
    def test_platform_url_returns_immediately(self):
        page = FakePage(["https://zenmux.ai/platform"], [])
        _run_with_patched_sleep(page)
        assert True

    def test_root_url_returns_immediately(self):
        page = FakePage(["https://zenmux.ai/"], [])
        _run_with_patched_sleep(page)
        assert True

    def test_verify_page_needverify_true_then_false_succeeds(self):
        """When needVerify is true then false, succeed."""
        responses = [
            {"status": 200, "body": {"success": True, "data": {"userId": "u1", "needVerify": True}}},
            {"status": 200, "body": {"success": True, "data": {"userId": "u1", "needVerify": False}}},
        ]
        page = FakePage(["https://zenmux.ai/verify?method=unknown"], responses)
        original_evaluate = page.evaluate

        def advance_after_eval(*args, **kwargs):
            result = original_evaluate(*args, **kwargs)
            # Simulate page redirecting to root after verification succeeds.
            if page._eval_index == len(responses):
                page._url_sequence = ["https://zenmux.ai/"]
            return result

        page.evaluate = advance_after_eval
        _run_with_patched_sleep(page)
        assert page._eval_index == 2

    def test_verify_page_timeout_when_needverify_stays_true(self):
        """When needVerify stays true, raise timeout."""
        responses = [
            {"status": 200, "body": {"success": True, "data": {"userId": "u1", "needVerify": True}}},
        ]
        page = FakePage(["https://zenmux.ai/verify?method=unknown"], responses)

        with pytest.raises(RuntimeError, match="等待登录跳转超时"):
            _run_with_patched_sleep(page, timeout=0)

    def test_verify_page_missing_needverify_treated_as_success(self):
        """If API doesn't return needVerify, treat userId as success."""
        responses = [
            {"status": 200, "body": {"success": True, "data": {"userId": "u1"}}},
        ]
        page = FakePage(["https://zenmux.ai/verify?method=unknown"], responses)
        original_evaluate = page.evaluate

        def advance_after_eval(*args, **kwargs):
            result = original_evaluate(*args, **kwargs)
            page._url_sequence = ["https://zenmux.ai/"]
            return result

        page.evaluate = advance_after_eval
        _run_with_patched_sleep(page)
        assert page._eval_index == 1

    def test_verify_page_no_user_id_continues_until_timeout(self):
        """If /api/user/info doesn't return userId, keep waiting until timeout."""
        responses = [
            {"status": 200, "body": {"success": True, "data": {}}},
        ]
        page = FakePage(["https://zenmux.ai/verify?method=unknown"], responses)

        with pytest.raises(RuntimeError, match="等待登录跳转超时"):
            _run_with_patched_sleep(page, timeout=0)

    def test_verify_page_api_error_continues_until_timeout(self):
        """If /api/user/info returns error, keep waiting until timeout."""
        responses = [
            {"error": "network failure"},
        ]
        page = FakePage(["https://zenmux.ai/verify?method=unknown"], responses)

        with pytest.raises(RuntimeError, match="等待登录跳转超时"):
            _run_with_patched_sleep(page, timeout=0)
