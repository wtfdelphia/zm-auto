"""Browser-based captcha solver (Playwright)."""
from __future__ import annotations

import os
import tempfile
import time
from typing import Any

import requests

from zm_auto.constants import USER_AGENT


def _remaining_ms(deadline: float, floor: int = 5000) -> int:
    return max(int((deadline - time.time()) * 1000), floor)


def _click_email_button(page: Any) -> None:
    """Click the email login button, handling multiple languages."""
    try:
        page.click("[class*='emailMethod']", timeout=5000)
        return
    except Exception:
        pass
    buttons = page.query_selector_all("button")
    for b in buttons:
        txt = (b.inner_text() or "").strip()
        if any(kw in txt for kw in [
            "Email", "email", "邮箱", "郵件", "メール", "이메일", "e-mail", "E-mail",
        ]):
            b.click()
            return
    if len(buttons) >= 4:
        buttons[3].click()


def solve_turnstile_browser(context: Any, page_url: str, timeout: int = 120) -> str:
    deadline = time.time() + timeout
    page = context.new_page()
    try:
        page.goto(page_url, wait_until="domcontentloaded", timeout=_remaining_ms(deadline))
        time.sleep(3)
        _click_email_button(page)
        time.sleep(2)
        page.wait_for_selector(
            '[name="cf-turnstile-response"]',
            timeout=_remaining_ms(deadline, 10000),
        )
        while time.time() < deadline:
            token = page.evaluate("""() => {
                const el = document.querySelector('[name=\"cf-turnstile-response\"]');
                return el ? el.value : '';
            }""")
            if token and len(token) > 10:
                return str(token)
            time.sleep(1.5)
        raise RuntimeError(f"Turnstile 浏览器超时 ({timeout}s)。尝试 provider=\"cdp\" 人工介入方案")
    finally:
        page.close()


def solve_recaptcha_browser(context: Any, page_url: str, timeout: int = 180) -> str:
    deadline = time.time() + timeout
    page = context.new_page()
    try:
        page.goto(page_url, wait_until="domcontentloaded", timeout=_remaining_ms(deadline))

        recaptcha_frame = page.wait_for_selector(
            "iframe[src*='google.com/recaptcha']",
            timeout=min(_remaining_ms(deadline), 30000),
        )
        frame = recaptcha_frame.content_frame()
        if not frame:
            raise RuntimeError("无法获取 reCAPTCHA iframe content_frame")

        checkbox = frame.wait_for_selector(
            ".recaptcha-checkbox-border", timeout=_remaining_ms(deadline, 10000)
        )
        checkbox.click()
        time.sleep(2)

        challenge_frame_el = frame.query_selector("iframe[src*='bframe']")
        if challenge_frame_el:
            challenge_frame = challenge_frame_el.content_frame()
            if not challenge_frame:
                raise RuntimeError("无法获取 reCAPTCHA challenge iframe")
            _solve_recaptcha_audio(challenge_frame, deadline, context)

        while time.time() < deadline:
            token = page.evaluate("""() => {
                const el = document.querySelector('#g-recaptcha-response');
                return el ? el.value : '';
            }""")
            if token:
                return str(token)
            time.sleep(1)
        raise RuntimeError(f"reCAPTCHA 浏览器超时 ({timeout}s)")
    finally:
        page.close()


def _solve_recaptcha_audio(frame: Any, deadline: float, context: Any) -> None:
    audio_btn = frame.wait_for_selector(
        "#recaptcha-audio-button", timeout=_remaining_ms(deadline, 10000)
    )
    audio_btn.click()
    time.sleep(2)

    audio_link = frame.wait_for_selector(
        ".rc-audiochallenge-tdownload-link", timeout=_remaining_ms(deadline, 10000)
    )
    audio_url = audio_link.get_attribute("href")
    if not audio_url:
        raise RuntimeError("无法获取 reCAPTCHA 音频下载链接")

    cookies = context.cookies()
    cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    resp = requests.get(
        audio_url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": frame.url,
            "Cookie": cookie_header,
        },
        timeout=_remaining_ms(deadline, 10000) / 1000.0,
    )
    resp.raise_for_status()
    audio_bytes = resp.content

    text = _recognize_audio(audio_bytes)

    response_input = frame.wait_for_selector(
        "#audio-response", timeout=_remaining_ms(deadline, 5000)
    )
    response_input.fill(text)

    verify_btn = frame.wait_for_selector(
        "#recaptcha-verify-button", timeout=_remaining_ms(deadline, 5000)
    )
    verify_btn.click()
    time.sleep(2)


def _recognize_audio(audio_bytes: bytes) -> str:
    try:
        import speech_recognition as sr
    except ImportError:
        raise RuntimeError("reCAPTCHA 音频识别需要 SpeechRecognition 库: pip install SpeechRecognition pydub")

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_path) as source:
            audio = recognizer.record(source)
        return str(recognizer.recognize_google(audio))
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
