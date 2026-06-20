"""Pydantic v2 configuration models."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .constants import CONFIG_FILE, DEFAULT_SITE_URL, USER_AGENT


class MailProviderBaseConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    enable: bool = False


class CloudflareTempEmailConfig(MailProviderBaseConfig):
    type: Literal["cloudflare_temp_email"] = "cloudflare_temp_email"  # type: ignore[assignment]
    api_base: str = ""
    admin_password: str = ""
    domain: list[str] = Field(default_factory=list)


class GptMailConfig(MailProviderBaseConfig):
    type: Literal["gptmail"] = "gptmail"  # type: ignore[assignment]
    api_key: str = ""
    default_domain: str = ""


class TempMailLolConfig(MailProviderBaseConfig):
    type: Literal["tempmail_lol"] = "tempmail_lol"  # type: ignore[assignment]
    api_key: str = ""
    domain: list[str] = Field(default_factory=list)


class DuckMailConfig(MailProviderBaseConfig):
    type: Literal["duckmail"] = "duckmail"  # type: ignore[assignment]
    api_key: str = ""
    default_domain: str = "duckmail.sbs"


class MoEmailConfig(MailProviderBaseConfig):
    type: Literal["moemail"] = "moemail"  # type: ignore[assignment]
    api_base: str = ""
    api_key: str = ""
    domain: list[str] = Field(default_factory=list)
    expiry_time: int = 0


class InbucketConfig(MailProviderBaseConfig):
    type: Literal["inbucket"] = "inbucket"  # type: ignore[assignment]
    api_base: str = ""
    domain: list[str] = Field(default_factory=list)
    random_subdomain: bool = True


class YydsMailConfig(MailProviderBaseConfig):
    type: Literal["yyds_mail"] = "yyds_mail"  # type: ignore[assignment]
    api_base: str = "https://maliapi.215.im/v1"
    api_key: str = ""
    domain: list[str] = Field(default_factory=list)
    subdomain: str = ""
    wildcard: bool = False


MailProviderConfig = (
    CloudflareTempEmailConfig
    | GptMailConfig
    | TempMailLolConfig
    | DuckMailConfig
    | MoEmailConfig
    | InbucketConfig
    | YydsMailConfig
)


class MailConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    request_timeout: int = 30
    wait_timeout: int = 120
    wait_interval: int = 2
    prefix: str = ""
    user_agent: str = USER_AGENT
    providers: list[MailProviderConfig] = Field(default_factory=list)

    @staticmethod
    def _discriminator(value: Any) -> str:
        if isinstance(value, BaseModel):
            return str(getattr(value, "type", ""))
        if isinstance(value, dict):
            return str(value.get("type", ""))
        return ""


class CaptchaBrowserConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    headless: bool = True
    stealth: bool = True
    user_data_dir: str = ""
    cdp_url: str = "http://127.0.0.1:9222"


class CaptchaConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    provider: str = "2captcha"
    api_key: str = ""
    browser: CaptchaBrowserConfig = Field(default_factory=CaptchaBrowserConfig)


class Sub2APIExportConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    base_url: str = ""
    notes_path: str = "/v1/chat/completions"
    openai_responses_supported: bool = True
    openai_responses_mode: str = "force_chat_completions"
    model_aliases: dict[str, str] = Field(default_factory=dict)


class Sub2APIConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool = False
    base_url: str = ""
    email: str = ""
    password: str = ""
    group_name: str = "auto"
    concurrency: int = 3
    models: list[str] = Field(
        default_factory=lambda: [
            "z-ai/glm-5.2-free",
            "moonshotai/kimi-k2.7-code-free",
        ]
    )
    upstream_base_url: str = ""
    export: Sub2APIExportConfig = Field(default_factory=Sub2APIExportConfig)


class Config(BaseModel):
    model_config = ConfigDict(extra="ignore")

    mail: MailConfig = Field(default_factory=MailConfig)
    proxy: str = ""
    total: int = 1
    threads: int = 1
    captcha: CaptchaConfig = Field(default_factory=CaptchaConfig)
    api_key_name: str = "auto"
    sub2api: Sub2APIConfig = Field(default_factory=Sub2APIConfig)
    site_url: str = DEFAULT_SITE_URL
    invite_code: str = ""
    logout_after: bool = True
    on_waitlist: str = "abort"
    waitlist_logout: bool = True
    auto_create_api_key: bool = False


def load_config(config_path: str | None = None) -> Config:
    """Load and validate config, merging with defaults."""
    path = Path(config_path) if config_path else CONFIG_FILE
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return Config(**data)
    return Config()


DEFAULT_CONFIG: dict[str, Any] = Config().model_dump()
