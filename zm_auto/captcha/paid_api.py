"""Paid captcha API solvers (2captcha / anticaptcha)."""
from __future__ import annotations

import time

import requests

from zm_auto.constants import RECAPTCHA_SITE_KEY, TURNSTILE_SITE_KEY


def _poll_2captcha(api_key: str, task_id: str, timeout: int) -> str:
    deadline = time.time() + timeout
    time.sleep(5)
    while time.time() < deadline:
        r = requests.get(
            "https://2captcha.com/res.php",
            params={"key": api_key, "action": "get", "id": task_id, "json": 1},
            timeout=30,
        )
        data = r.json()
        if data.get("status") == 1:
            return str(data["request"])
        if data.get("request") != "CAPCHA_NOT_READY":
            raise RuntimeError(f"2captcha 轮询失败: {data}")
        time.sleep(5)
    raise RuntimeError(f"2captcha 超时 ({timeout}s)")


def solve_2captcha_turnstile(api_key: str, page_url: str, timeout: int = 120) -> str:
    r = requests.post(
        "https://2captcha.com/in.php",
        data={
            "key": api_key,
            "method": "turnstile",
            "sitekey": TURNSTILE_SITE_KEY,
            "pageurl": page_url,
            "json": 1,
        },
        timeout=30,
    )
    data = r.json()
    if data.get("status") != 1:
        raise RuntimeError(f"2captcha Turnstile 提交失败: {data}")
    return _poll_2captcha(api_key, data["request"], timeout)


def solve_2captcha_recaptcha(api_key: str, page_url: str, timeout: int = 180) -> str:
    r = requests.get(
        "https://2captcha.com/in.php",
        params={
            "key": api_key,
            "method": "userrecaptcha",
            "googlekey": RECAPTCHA_SITE_KEY,
            "pageurl": page_url,
            "json": 1,
        },
        timeout=30,
    )
    data = r.json()
    if data.get("status") != 1:
        raise RuntimeError(f"2captcha reCAPTCHA 提交失败: {data}")
    return _poll_2captcha(api_key, data["request"], timeout)


def _poll_anticaptcha(api_key: str, task_id: str, timeout: int) -> str:
    deadline = time.time() + timeout
    time.sleep(5)
    while time.time() < deadline:
        r = requests.post(
            "https://api.anti-captcha.com/getTaskResult",
            json={"clientKey": api_key, "taskId": task_id},
            timeout=30,
        )
        data = r.json()
        if data.get("errorId"):
            raise RuntimeError(f"anticaptcha 轮询失败: {data.get('errorDescription')}")
        if data.get("status") == "ready":
            return str(data["solution"]["gRecaptchaResponse"])
        time.sleep(5)
    raise RuntimeError(f"anticaptcha 超时 ({timeout}s)")


def solve_anticaptcha_recaptcha(api_key: str, page_url: str, timeout: int = 180) -> str:
    r = requests.post(
        "https://api.anti-captcha.com/createTask",
        json={
            "clientKey": api_key,
            "task": {
                "type": "NoCaptchaTaskProxyless",
                "websiteURL": page_url,
                "websiteKey": RECAPTCHA_SITE_KEY,
            },
        },
        timeout=30,
    )
    data = r.json()
    if data.get("errorId"):
        raise RuntimeError(f"anticaptcha 提交失败: {data.get('errorDescription')}")
    return _poll_anticaptcha(api_key, data["taskId"], timeout)
