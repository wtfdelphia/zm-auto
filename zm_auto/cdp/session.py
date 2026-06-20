"""CDP session context manager with multi-tab support.

借鉴 bb-browser `packages/daemon/src/cdp-connection.ts` 的设计思想：
把 CDP 连接、target 发现、资源释放封装成类，避免连接泄漏，并提供友好的错误提示。

新增借鉴点：
- 多 tab 短 ID 管理（bb-browser per-tab 事件隔离）
- 录制数据 seq/request_id/trigger 因果链（bb-browser trace timeline）
"""
from __future__ import annotations

from typing import Any

from zm_auto.exceptions import ZMError

from .har import build_har
from .helpers import _cdp_connect, _cdp_new_page
from .recording import RecordingBuffer
from .stealth import STEALTH_SCRIPT
from .tab import Tab, generate_short_id


class CDPSession:
    """Context manager for a CDP Playwright session.

    支持两种用法：
        # 1) 上下文管理器
        with CDPSession(cdp_url, cookies) as session:
            page = session.page
            ...

        # 2) 手动 open/close
        session = CDPSession(cdp_url)
        session.open()
        try:
            page = session.page
            ...
        finally:
            session.close()
    """

    def __init__(
        self,
        cdp_url: str | None = None,
        cookies: list[dict] | None = None,
        *,
        timeout: float = 30.0,
    ) -> None:
        self.cdp_url = cdp_url or "http://127.0.0.1:9222"
        self.cookies = cookies
        self.timeout = timeout
        self._pw: Any = None
        self._browser: Any = None
        self._tabs: dict[str, Tab] = {}
        self._active_tab_id: str | None = None
        self._recording_enabled: bool = False

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def open(self) -> "CDPSession":
        """打开 CDP 连接并新建首个 tab；可重复调用（已打开时忽略）。"""
        if self._browser is not None:
            return self
        try:
            self._pw, self._browser = _cdp_connect(self.cdp_url)
        except Exception as exc:
            raise ZMError(
                message=f"无法连接 CDP: {exc}",
                hint=f"请确认 Chrome 已启动并开启 --remote-debugging-port={self.cdp_url.split(':')[-1].split('/')[0]}",
            ) from exc
        try:
            self._new_tab_internal()
        except Exception as exc:
            self.close()
            raise ZMError(
                message=f"CDP 新建页面失败: {exc}",
                hint="请检查 Chrome 是否处于正常状态。",
            ) from exc
        return self

    def __enter__(self) -> "CDPSession":
        return self.open()

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    @property
    def page(self) -> Any:
        if self._active_tab_id is None:
            raise RuntimeError("CDPSession 没有打开的 tab")
        return self._tabs[self._active_tab_id].page

    @property
    def browser(self) -> Any:
        if self._browser is None:
            raise RuntimeError("CDPSession is not open")
        return self._browser

    def new_page(self) -> Any:
        """兼容旧 API：创建一个新 tab 并返回其 page。"""
        return self.new_tab()

    def new_tab(self) -> Any:
        """创建新 tab，返回其 page。"""
        if self._browser is None:
            self.open()
            assert self._active_tab_id is not None
            return self._tabs[self._active_tab_id].page
        return self._new_tab_internal()

    def _new_tab_internal(self) -> Any:
        page = _cdp_new_page(self._browser, self.cookies)
        tab_id = self._allocate_tab_id()
        self._tabs[tab_id] = Tab(tab_id=tab_id, page=page)
        self._active_tab_id = tab_id
        if self._recording_enabled:
            self._attach_recording(page)
        return page

    def _allocate_tab_id(self) -> str:
        for _ in range(100):
            tab_id = generate_short_id(4)
            if tab_id not in self._tabs:
                return tab_id
        raise RuntimeError("无法为 tab 分配短 ID")

    def switch_tab(self, tab_id: str) -> None:
        """切换到指定 tab。"""
        if tab_id not in self._tabs:
            raise ValueError(f"未知 tab id: {tab_id}")
        self._active_tab_id = tab_id

    def close_tab(self, tab_id: str) -> None:
        """关闭指定 tab。"""
        tab = self._tabs.pop(tab_id, None)
        if tab is None:
            return
        try:
            tab.page.close()
        except Exception:
            pass
        if self._active_tab_id == tab_id:
            # Fall back to any remaining tab
            self._active_tab_id = next(iter(self._tabs), None)

    def list_tabs(self) -> list[str]:
        """返回所有 tab 短 ID 列表。"""
        return list(self._tabs.keys())

    def close(self) -> None:
        """按 tab → browser → playwright 顺序安全关闭，忽略所有异常。"""
        for tab in list(self._tabs.values()):
            try:
                tab.page.close()
            except Exception:
                pass
        self._tabs.clear()
        self._active_tab_id = None
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._pw is not None:
            try:
                self._pw.stop()
            except Exception:
                pass
            self._pw = None

    def __del__(self) -> None:
        # 尽最大努力防止资源泄漏；close() 已做异常保护。
        if self._browser is not None or self._pw is not None or self._tabs:
            self.close()

    # ------------------------------------------------------------------ #
    # Network recording (HAR-like)
    # ------------------------------------------------------------------ #
    def _active_recording(self, *, create: bool = False) -> RecordingBuffer:
        if self._active_tab_id is None and not create:
            raise RuntimeError("CDPSession 没有打开的 tab")
        if self._active_tab_id is None:
            # Used during direct _attach_recording calls in tests without a real browser.
            tab_id = self._allocate_tab_id()
            self._tabs[tab_id] = Tab(tab_id=tab_id, page=None)
            self._active_tab_id = tab_id
        return self._tabs[self._active_tab_id].recording

    def enable_recording(self) -> "CDPSession":
        """开启网络请求录制。对已经打开的 page 也会立即生效。"""
        self._recording_enabled = True
        if self._active_tab_id is not None:
            tab = self._tabs[self._active_tab_id]
            self._attach_recording(tab.page)
        return self

    def disable_recording(self) -> "CDPSession":
        """关闭网络请求录制，但不清理已有记录。"""
        self._recording_enabled = False
        return self

    def get_recording(self, *, tab_id: str | None = None) -> list[dict[str, Any]]:
        """获取录制到的请求/响应列表。"""
        if tab_id is not None:
            if tab_id not in self._tabs:
                raise ValueError(f"未知 tab id: {tab_id}")
            return self._tabs[tab_id].recording.to_dicts()
        # If no tab is open (e.g. unit tests without a browser), return empty list.
        if self._active_tab_id is None:
            return []
        return self._active_recording().to_dicts()

    def clear_recording(self) -> "CDPSession":
        """清空当前活跃 tab 的录制记录。"""
        if self._active_tab_id is not None:
            self._active_recording().clear()
        return self

    def mark_trigger(self, name: str) -> int:
        """在当前活跃 tab 的录制中标记一个 trigger。"""
        return self._active_recording().mark_trigger(name)

    def export_har(self, *, tab_id: str | None = None, title: str = "zm-auto") -> dict[str, Any]:
        """将当前（或指定 tab）的录制数据导出为 HAR 1.2 对象。"""
        return build_har(self.get_recording(tab_id=tab_id), title=title)

    def add_stealth_scripts(self, page: Any) -> None:
        """为 page 注入反检测脚本。"""
        if page is None:
            return
        try:
            page.add_init_script(STEALTH_SCRIPT)
        except Exception:
            # If add_init_script is unavailable (e.g. remote CDP), ignore.
            pass

    def _attach_recording(self, page: Any) -> None:
        if self._active_tab_id is None:
            # Test path: create a dummy tab so recording has a buffer.
            tab_id = self._allocate_tab_id()
            self._tabs[tab_id] = Tab(tab_id=tab_id, page=page)
            self._active_tab_id = tab_id
        pending: dict[str, str] = {}

        def _on_request(request: Any) -> None:
            try:
                request_id = self._active_recording().add_request(
                    method=request.method,
                    url=request.url,
                )
                pending[request.url] = request_id
            except Exception:
                pass

        def _on_response(response: Any) -> None:
            try:
                request = response.request
                request_id = pending.pop(request.url, "")
                self._active_recording().add_response(
                    method=request.method,
                    url=response.url,
                    status=response.status,
                    request_id=request_id,
                )
            except Exception:
                pass

        page.on("request", _on_request)
        page.on("response", _on_response)
