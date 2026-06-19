"""Tests for sub2api_importer module."""

import pytest
from sub2api_importer import Sub2APIImporter


class TestSub2APIImporterInit:
    """Test Sub2APIImporter constructor and defaults."""

    def test_empty_config_defaults(self):
        """Empty config should use safe defaults without crashing."""
        importer = Sub2APIImporter({})
        assert importer.base_url == ""
        assert importer.email == ""
        assert importer.password == ""
        assert importer.group_name == "auto"
        assert importer.concurrency == 3
        assert importer.models == []
        assert importer._token == ""
        assert importer._group_id == 0

    def test_full_config(self):
        """Full config should set all fields correctly."""
        cfg = {
            "base_url": "https://sub2api.example.com",
            "email": "test@example.com",
            "password": "secret",
            "group_name": "mygroup",
            "concurrency": 5,
            "models": ["model-a", "model-b"],
            "upstream_base_url": "https://upstream.example.com/api",
        }
        importer = Sub2APIImporter(cfg)
        assert importer.base_url == "https://sub2api.example.com"
        assert importer.email == "test@example.com"
        assert importer.password == "secret"
        assert importer.group_name == "mygroup"
        assert importer.concurrency == 5
        assert importer.models == ["model-a", "model-b"]
        assert importer.upstream_base_url == "https://upstream.example.com/api"

    def test_concurrency_string_conversion(self):
        """Concurrency from string config should be cast to int."""
        importer = Sub2APIImporter({"concurrency": "10"})
        assert importer.concurrency == 10
        assert isinstance(importer.concurrency, int)

    def test_base_url_trailing_slash_stripped(self):
        """Base URL trailing slash should be stripped."""
        importer = Sub2APIImporter({"base_url": "https://example.com/"})
        assert importer.base_url == "https://example.com"

    def test_headers_raises_without_token(self):
        """Accessing headers before login should raise RuntimeError."""
        importer = Sub2APIImporter({})
        with pytest.raises(RuntimeError, match="未登录"):
            _ = importer.headers

    def test_models_list_copied_not_shared(self):
        """Models list should be a copy, not a reference to the input."""
        original = ["model-x"]
        importer = Sub2APIImporter({"models": original})
        original.append("model-y")
        assert importer.models == ["model-x"]
