"""Shared CDP helper functions."""
from __future__ import annotations

from typing import Any


def _cdp_connect(cdp_url: str) -> tuple[Any, Any]:
    """Connect to a Chrome via CDP. Returns (playwright, browser)."""
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(cdp_url)
    return pw, browser


def _cdp_new_page(browser: Any, cookies: list[dict] | None = None) -> Any:
    """Create a new page in the CDP browser, optionally injecting cookies."""
    if browser.contexts:
        page = browser.contexts[0].new_page()
    else:
        page = browser.new_page()
    if cookies:
        page.context.add_cookies(cookies)
    return page


def _extract_cookies(page: Any, site_domain: str | None = None) -> dict[str, str]:
    """Extract cookies for a given domain from a CDP page."""
    from urllib.parse import urlparse

    if site_domain is None:
        site_domain = "." + urlparse(page.url).netloc
    bare_domain = site_domain.lstrip(".")
    return {
        c["name"]: c["value"]
        for c in page.context.cookies()
        if c.get("domain", "").endswith((site_domain, bare_domain))
    }
