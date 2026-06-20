"""Tests for CDPSession multi-tab management."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from zm_auto.cdp.session import CDPSession
from zm_auto.cdp.tab import generate_short_id


def _make_session() -> CDPSession:
    session = CDPSession()
    session._browser = MagicMock()
    session._browser.contexts = []
    return session


def test_generate_short_id_length() -> None:
    tab_id = generate_short_id(4)
    assert len(tab_id) == 4
    assert all(c in "0123456789abcdef" for c in tab_id)


def test_short_id_uniqueness() -> None:
    ids = {generate_short_id(6) for _ in range(100)}
    assert len(ids) == 100


def test_new_tab_creates_short_id() -> None:
    session = _make_session()
    page = MagicMock()
    session._browser.new_page.return_value = page
    returned = session.new_tab()
    assert returned is page
    assert len(session.list_tabs()) == 1
    tab_id = session.list_tabs()[0]
    assert len(tab_id) == 4
    assert session._active_tab_id == tab_id


def test_switch_tab() -> None:
    session = _make_session()
    page1 = MagicMock()
    page2 = MagicMock()
    session._browser.new_page.side_effect = [page1, page2]
    session.new_tab()
    tab_id1 = session.list_tabs()[0]
    session.new_tab()
    tab_id2 = session.list_tabs()[1]
    assert session._active_tab_id == tab_id2
    session.switch_tab(tab_id1)
    assert session._active_tab_id == tab_id1
    assert session.page is page1


def test_close_tab_switches_active() -> None:
    session = _make_session()
    page1 = MagicMock()
    page2 = MagicMock()
    session._browser.new_page.side_effect = [page1, page2]
    session.new_tab()
    tab_id1 = session.list_tabs()[0]
    session.new_tab()
    tab_id2 = session.list_tabs()[1]
    session.close_tab(tab_id2)
    assert tab_id2 not in session.list_tabs()
    assert session._active_tab_id == tab_id1


def test_close_all_tabs_on_close() -> None:
    session = _make_session()
    session._pw = MagicMock()
    page1 = MagicMock()
    page2 = MagicMock()
    session._browser.new_page.side_effect = [page1, page2]
    session.new_tab()
    session.new_tab()
    session.close()
    page1.close.assert_called_once()
    page2.close.assert_called_once()
    assert not session.list_tabs()


def test_page_without_tab_raises() -> None:
    session = CDPSession()
    with pytest.raises(RuntimeError):
        _ = session.page
