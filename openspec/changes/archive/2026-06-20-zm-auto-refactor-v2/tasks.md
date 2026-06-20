## Tasks

### 1. CDP Tab 管理

- [x] 1.1 创建 `zm_auto/cdp/tab.py`，定义 `_Tab` dataclass 和短 ID 生成器 `_generate_short_id()`。
- [x] 1.2 扩展 `CDPSession`，新增 `_tabs: dict[str, _Tab]`、`_active_tab_id: str | None`、`_seq: int`。
- [x] 1.3 实现 `new_tab()`、`switch_tab(tab_id)`、`close_tab(tab_id)`、`list_tabs()`。
- [x] 1.4 重构 `page` 属性返回当前活跃 tab 的 page；`new_page()` 保留为 `new_tab()` 的别名。
- [x] 1.5 实现 `__exit__` / `close()` 关闭所有 tab 并释放 browser。
- [x] 1.6 新增 `tests/test_cdp_tab.py`：验证短 ID 生成、多 tab 切换、关闭 session 释放资源。

### 2. CDP 录制增强

- [x] 2.1 创建 `zm_auto/cdp/recording.py`，定义 `RecordingEntry`、`RequestEntry`、`ResponseEntry`、`TriggerEntry` dataclass。
- [x] 2.2 将 `CDPSession._recording` 从 dict 列表改为 `RecordingEntry` 列表；按当前活跃 tab 隔离。
- [x] 2.3 为每个事件分配单调递增 `seq`，request/response 使用相同 `request_id` 配对。
- [x] 2.4 实现 `mark_trigger(name)` 在录制中插入 trigger 条目，后续 request/response 携带 `trigger_seq`。
- [x] 2.5 更新 `export_har()` 以兼容增强后的录制数据结构。
- [x] 2.6 新增 `tests/test_cdp_recording.py`：验证 seq 单调、request/response 配对、trigger 因果链。

### 3. Site Adapter 注册表

- [x] 3.1 创建 `zm_auto/sites/base.py`，定义 `BaseSiteAdapter` 抽象类。
- [x] 3.2 创建 `zm_auto/sites/zenmux.py`，实现 `ZenmuxAdapter`，迁移硬编码的 zenmux 站点 URL 和路径。
- [x] 3.3 创建 `zm_auto/sites/__init__.py`，通过 `__subclasses__()` 自动发现 adapter，提供 `get_site_adapter(name)` 和 `get_adapter_for_url(url)`。
- [x] 3.4 在 `zm_auto/services/registrar.py` 中使用 adapter 获取站点 URL 和端点。
- [x] 3.5 在 `zm_auto/services/user_info` 中使用 adapter 获取站点 URL 和 CDP 相关路径。
- [x] 3.6 新增 `tests/test_sites.py`：验证 adapter 自动发现、按 name/URL 获取。

### 4. Agent Skill Schema

- [x] 4.1 完善 `zm_auto/cli/commands.py` 中 `ParamDef.to_json_schema()`，支持 boolean/number/string 类型映射，生成标准 JSON Schema。
- [x] 4.2 确保 `registry_json_schema()` 输出 OpenAI function-calling 风格对象。
- [x] 4.3 新增 `zm_auto/cli/skills.py` 子命令 handler，支持 `--format json|compact`。
- [x] 4.4 在 `zm_auto/cli/__init__.py` 中注册 `skills` 子命令。
- [x] 4.5 新增 `tests/test_cli_skills.py`：验证 JSON 输出字段、compact 格式。

### 5. Obstacle Course 回归套件

- [x] 5.1 创建 `tests/obstacle_course/conftest.py`，用标准库 `http.server` 启动本地 fixtures 服务。
- [x] 5.2 实现 `/api/user/info`、`/api/api_key/list` 等端点，返回固定 successful 响应。
- [x] 5.3 创建 `tests/obstacle_course/test_register_flow.py`，使用本地服务验证 send-code 端点。
- [x] 5.4 创建 `tests/obstacle_course/test_cdp_flow.py`，验证本地 fixtures 服务可达。
- [x] 5.5 将 obstacle course 加入 pytest 收集路径，确保 `pytest tests/` 自动执行。

### 6. 验证与收尾

- [x] 6.1 `python -m compileall zm_auto/`
- [x] 6.2 `ruff check zm_auto/ tests/`
- [x] 6.3 `mypy zm_auto/`
- [x] 6.4 `python -m pytest tests/ -v` 全绿
- [x] 6.5 `python -m zm_auto skills --format json` 正常输出
- [x] 6.6 更新 `README.md` / `AGENTS.md` 中新增的 `skills` 命令和 site adapter 说明
- [x] 6.7 `openspec validate --all`
- [x] 6.8 `spec-compliance-check`
- [x] 6.9 `verification-before-completion`
