"""Project-wide constants."""
from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.json"

X_API_VERSION = "2026-04-20"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

CDP_URL = "http://127.0.0.1:9222"
DEFAULT_SITE_URL = "https://example.com"

# Captcha site keys
TURNSTILE_SITE_KEY = "0x4AAAAAAB3vWB8HhhtIcASj"
RECAPTCHA_SITE_KEY = "6LdN_REsAAAAAKSlH2k4VNXoCT-Fi1bv_Ufaf86t"
