"""Mail provider factory."""
from __future__ import annotations

__all__ = [
    "BaseMailProvider",
    "create_mailbox",
    "wait_for_code",
    "_config",
    "_random_mailbox_name",
    "_random_subdomain_label",
    "_next_domain",
    "_parse_received_at",
    "_extract_content",
    "_extract_text_candidates",
    "_message_matches_email",
    "_extract_code",
    "_message_tracking_ref",
    "_entries",
    "_enabled_entries",
    "_next_entry",
    "_create_provider",
    "_FORBIDDEN_CODES",
]



from typing import TYPE_CHECKING, Any

from .base import (
    _FORBIDDEN_CODES,
    BaseMailProvider,
    _config,
    _extract_code,
    _extract_content,
    _extract_text_candidates,
    _message_matches_email,
    _message_tracking_ref,
    _next_domain,
    _parse_received_at,
    _random_mailbox_name,
    _random_subdomain_label,
    provider_index,
    provider_lock,
)

# Import all provider classes so they register themselves.
from .cloudflare import CloudflareTempMailProvider  # noqa: F401
from .duckmail import DuckMailProvider  # noqa: F401
from .gptmail import GptMailProvider  # noqa: F401
from .inbucket import InbucketMailProvider  # noqa: F401
from .moemail import MoEmailProvider  # noqa: F401
from .tempmail_lol import TempMailLolProvider  # noqa: F401
from .yyds import YydsMailProvider  # noqa: F401

if TYPE_CHECKING:
    from typing import Any



# --------------------------------------------------------------------------- #
# Provider factory + public API
# --------------------------------------------------------------------------- #
def _provider_registry() -> dict[str, type[BaseMailProvider]]:
    return {cls.type: cls for cls in BaseMailProvider.__subclasses__() if cls.type}  # type: ignore[type-abstract]


def _entries(mail_config: dict) -> list[dict]:
    return [{**item, "provider_ref": f"{item['type']}#{index + 1}"} for index, item in enumerate(mail_config["providers"])]


def _enabled_entries(mail_config: dict) -> list[dict]:
    items = [item for item in _entries(mail_config) if item.get("enable")]
    if not items:
        raise RuntimeError("mail.providers 没有启用的 provider")
    return items


def _next_entry(mail_config: dict) -> dict:
    global provider_index
    items = _enabled_entries(mail_config)
    if len(items) == 1:
        return dict(items[0])
    with provider_lock:
        value = dict(items[provider_index % len(items)])
        provider_index = (provider_index + 1) % len(items)
        return value


def _create_provider(mail_config: dict, provider: str = "", provider_ref: str = "", proxy: str = "") -> BaseMailProvider:
    entry = next(
        (dict(item) for item in _entries(mail_config) if provider_ref and item["provider_ref"] == provider_ref),
        None,
    )
    entry = (
        entry
        or next(
            (dict(item) for item in _enabled_entries(mail_config) if provider and item["type"] == provider),
            None,
        )
        or _next_entry(mail_config)
    )
    conf = _config(mail_config)
    registry = _provider_registry()
    cls = registry.get(entry["type"])
    if not cls:
        raise RuntimeError(f"不支持的 mail.provider: {entry['type']}")
    cls.validate_config(entry)
    return cls(entry, conf, proxy)  # type: ignore[call-arg, arg-type]


def create_mailbox(mail_config: dict, username: str | None = None, proxy: str = "") -> dict[str, Any]:
    provider = _create_provider(mail_config, proxy=proxy)
    try:
        return provider.create_mailbox(username)  # type: ignore[no-any-return]
    finally:
        provider.close()


def wait_for_code(mail_config: dict, mailbox: dict, proxy: str = "") -> str | None:
    provider = _create_provider(
        mail_config,
        provider=str(mailbox.get("provider") or ""),
        provider_ref=str(mailbox.get("provider_ref") or ""),
        proxy=proxy,
    )
    try:
        return provider.wait_for_code(mailbox)
    finally:
        provider.close()

