"""Tests for register.py config and helpers (no network calls)."""

import json
from unittest.mock import patch


from zm_auto.config import DEFAULT_CONFIG, load_config
from zm_auto.constants import BASE_DIR, CONFIG_FILE, USER_AGENT, X_API_VERSION
from zm_auto.http import make_session
import zm_auto.services.registrar
from zm_auto.services.registrar_core import _api_headers, log, save_results, step


# --------------------------------------------------------------------------- #
# DEFAULT_CONFIG
# --------------------------------------------------------------------------- #
class TestDefaultConfig:
    def test_has_required_keys(self):
        required = [
            "mail", "proxy", "total", "threads", "captcha",
            "api_key_name", "site_url", "invite_code", "logout_after",
            "on_waitlist", "waitlist_logout", "sub2api",
        ]
        for key in required:
            assert key in DEFAULT_CONFIG, f"Missing key: {key}"

    def test_mail_defaults(self):
        mail = DEFAULT_CONFIG["mail"]
        assert mail["request_timeout"] == 30
        assert mail["wait_timeout"] == 120
        assert mail["wait_interval"] == 2
        assert isinstance(mail["providers"], list)

    def test_captcha_defaults(self):
        captcha = DEFAULT_CONFIG["captcha"]
        assert captcha["provider"] == "2captcha"
        assert captcha["api_key"] == ""
        assert captcha["browser"]["headless"] is True
        assert captcha["browser"]["stealth"] is True

    def test_sub2api_defaults(self):
        sub2api = DEFAULT_CONFIG["sub2api"]
        assert sub2api["enabled"] is False
        assert sub2api["group_name"] == "auto"
        assert sub2api["concurrency"] == 3
        assert isinstance(sub2api["models"], list)

    def test_site_url_default(self):
        assert DEFAULT_CONFIG["site_url"] == "https://example.com"

    def test_on_waitlist_default(self):
        assert DEFAULT_CONFIG["on_waitlist"] == "abort"


# --------------------------------------------------------------------------- #
# load_config
# --------------------------------------------------------------------------- #
class TestLoadConfig:
    @patch("pathlib.Path.exists", return_value=False)
    def test_returns_defaults_when_no_config_file(self, mock_exists):
        config = load_config()
        assert config.site_url == "https://example.com"
        assert config.total == 1
        assert config.threads == 1

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.read_text")
    def test_merges_saved_config(self, mock_read, mock_exists):
        saved = {"site_url": "https://custom.example.com", "total": 5, "threads": 2}
        mock_read.return_value = json.dumps(saved)
        config = load_config()
        assert config.site_url == "https://custom.example.com"
        assert config.total == 5
        assert config.threads == 2
        assert config.mail.wait_timeout == 120

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.read_text")
    def test_partial_saved_config_keeps_other_defaults(self, mock_read, mock_exists):
        saved = {"total": 10}
        mock_read.return_value = json.dumps(saved)
        config = load_config()
        assert config.total == 10
        assert config.threads == 1
        assert config.captcha.provider == "2captcha"

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.read_text")
    def test_extra_keys_in_saved_config_ignored(self, mock_read, mock_exists):
        saved = {"site_url": "https://example.com", "unknown_key": "should_be_ignored"}
        mock_read.return_value = json.dumps(saved)
        config = load_config()
        assert "unknown_key" not in config.model_dump()
        assert config.site_url == "https://example.com"


# --------------------------------------------------------------------------- #
# API helpers
# --------------------------------------------------------------------------- #
class TestApiHelpers:
    def test_make_session_no_proxy(self):
        session = make_session()
        assert session is not None

    def test_make_session_with_proxy(self):
        session = make_session(proxy="http://127.0.0.1:7890")
        assert session is not None
        assert session.proxies == {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}

    def test_api_headers_default(self):
        headers = _api_headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["x-api-version"] == X_API_VERSION
        assert "Referer" not in headers

    def test_api_headers_with_referer(self):
        headers = _api_headers(referer="https://example.com/login")
        assert headers["Referer"] == "https://example.com/login"
        assert headers["Content-Type"] == "application/json"


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
class TestConstants:
    def test_x_api_version(self):
        assert X_API_VERSION == "2026-04-20"

    def test_user_agent_is_nonempty(self):
        assert len(USER_AGENT) > 0
        assert "Chrome" in USER_AGENT

    def test_base_dir_is_absolute(self):
        assert BASE_DIR.is_absolute()

    def test_config_file_path(self):
        assert CONFIG_FILE.name == "config.json"


# --------------------------------------------------------------------------- #
# log / step helpers
# --------------------------------------------------------------------------- #
class TestLogging:
    def test_log_does_not_raise(self, caplog):
        with caplog.at_level("INFO"):
            log("test message")
        assert "test message" in caplog.text

    def test_log_with_color(self, caplog):
        with caplog.at_level("INFO"):
            log("error message", "red")
        assert "error message" in caplog.text

    def test_step_does_not_raise(self, caplog):
        with caplog.at_level("INFO"):
            step(1, "starting task")
        assert "[任务1]" in caplog.text
        assert "starting task" in caplog.text


# --------------------------------------------------------------------------- #
# save_results
# --------------------------------------------------------------------------- #
class TestSaveResults:
    def test_creates_file_with_results(self, tmp_path, monkeypatch):
        monkeypatch.setattr(zm_auto.services.registrar_core, "BASE_DIR", tmp_path)
        results = [{"ok": True, "result": {"email": "test@example.com", "api_key": "sk-xxx"}}]
        path = save_results(results)
        assert path.exists()
        data = json.loads(path.read_text())
        assert len(data) == 1
        assert data[0]["email"] == "test@example.com"

    def test_empty_results(self, tmp_path, monkeypatch):
        monkeypatch.setattr(zm_auto.services.registrar_core, "BASE_DIR", tmp_path)
        path = save_results([])
        assert path.exists()
        data = json.loads(path.read_text())
        assert data == []

    def test_filename_is_accounts_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(zm_auto.services.registrar_core, "BASE_DIR", tmp_path)
        path = save_results([{"ok": True, "result": {"email": "x"}}])
        assert path.name == "accounts.json"
