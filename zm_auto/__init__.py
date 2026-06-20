"""zm-auto package.

Public API:
    load_config     -> zm_auto.config.load_config
    ZMError         -> zm_auto.exceptions.ZMError
    make_session    -> zm_auto.http.make_session
    CDPSession      -> zm_auto.cdp.session.CDPSession
    BaseMailProvider, create_mailbox, wait_for_code -> zm_auto.providers
    CaptchaSolver -> zm_auto.captcha.CaptchaSolver
"""
from __future__ import annotations

from zm_auto.captcha import CaptchaSolver
from zm_auto.cdp.session import CDPSession
from zm_auto.config import load_config
from zm_auto.exceptions import ZMError
from zm_auto.http import make_session
from zm_auto.providers import BaseMailProvider, create_mailbox, wait_for_code

__all__ = [
    "__version__",
    "load_config",
    "ZMError",
    "make_session",
    "CDPSession",
    "BaseMailProvider",
    "create_mailbox",
    "wait_for_code",
    "CaptchaSolver",
]

__version__ = "0.1.0"
