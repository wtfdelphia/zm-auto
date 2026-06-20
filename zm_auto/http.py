"""HTTP session factory."""
from __future__ import annotations

import urllib3
from curl_cffi import requests as curl_requests

from .constants import USER_AGENT

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def make_session(proxy: str = "", headers: dict[str, str] | None = None) -> curl_requests.Session:
    """Create a curl_cffi session with optional proxy and headers."""
    session: curl_requests.Session = curl_requests.Session(impersonate="chrome")
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    if headers:
        session.headers.update(headers)
    if "User-Agent" not in session.headers:
        session.headers["User-Agent"] = USER_AGENT
    return session
