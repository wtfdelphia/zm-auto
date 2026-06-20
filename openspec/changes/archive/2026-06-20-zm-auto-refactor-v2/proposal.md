## Why

`refactor-zm-auto-package` 和 `zm-auto-browser-polish` 已经把脚本重构成结构化的 `zm_auto/` 包，并补齐了 CDP 录制、stealth 注入和错误重试。通过深度对比本地 `bb-browser`、`obscura` 和 `browser-act/skills` 三个项目，zm-auto 在多 tab 管理、录制可追溯性、站点适配和回归测试方面仍有明显可借鉴空间。本次变更在这些方向上做最小化、无外部依赖的增强，让 CDP 层和 CLI 层更接近“Agent-first 浏览器自动化工具”的成熟度。

## What Changes

- **多 Tab CDP 管理**：扩展 `CDPSession`，引入短 ID 管理的 tab 列表，支持 `new_tab()` / `close_tab(tab_id)` / `switch_tab(tab_id)`，每个 tab 的录制、事件、生命周期相互隔离（借鉴 bb-browser per-tab 事件隔离）。
- **录制数据增强**：为录制条目增加单调递增的 `seq`、请求/响应配对、以及 `trigger` 因果链字段，方便离线追溯哪次点击触发了哪些网络请求（借鉴 bb-browser trace timeline）。
- **站点适配器注册表**：将当前硬编码在 `services/registrar.py` 和 `services/user_info` 中的 zenmux 站点逻辑抽象为 `zm_auto/sites/base.py` + `zm_auto/sites/zenmux.py`，并通过 `__subclasses__()` 自动发现（与 provider 注册方式一致，借鉴 bb-browser site-adapter）。
- **AI Agent Skill Schema 导出**：扩展 `zm_auto/cli/commands.py` 的 `registry_json_schema()`，输出符合 browser-act / OpenAI function 风格的调用 schema，并新增 CLI 子命令 `skills` 打印 schema（借鉴 browser-act `get-skills`）。
- **Obstacle Course 回归套件（离线 fixtures）**：新增 `tests/obstacle_course/` 目录，用本地 Flask/Werkzeug 或纯 `http.server` fixtures 模拟目标站点的注册流程，作为真实站点回归的第一道防线（借鉴 obscura obstacle course）。

## Capabilities

### New Capabilities

- `cdp-tab-management`: `CDPSession` 支持多 tab 短 ID 管理与生命周期隔离。
- `cdp-recording-enhanced`: 录制数据支持 seq、请求/响应配对、trigger 因果链。
- `site-adapter-registry`: 可插拔的站点适配器注册表，统一处理不同目标站点。
- `agent-skills-schema`: 从 CLI 命令注册表自动生成 AI Agent 可调用的技能 schema。
- `obstacle-course`: 基于离线 fixtures 的回归测试套件，验证注册/CDP 链路。

### Modified Capabilities

- `cdp-session`: 扩展 `CDPSession` API 以支持多 tab 与增强录制。
- `cli-interface`: 新增 `skills` 子命令，扩展 `doctor` 以展示 tab/adapter 信息。

## Impact

- 新增模块：
  - `zm_auto/cdp/tab.py`
  - `zm_auto/cdp/recording.py`
  - `zm_auto/sites/base.py`
  - `zm_auto/sites/zenmux.py`
  - `zm_auto/sites/__init__.py`
  - `tests/obstacle_course/conftest.py`
  - `tests/obstacle_course/test_register_flow.py`
- 修改模块：
  - `zm_auto/cdp/session.py`（tab 管理、增强录制）
  - `zm_auto/cli/commands.py`（skill schema 导出）
  - `zm_auto/cli/__init__.py`（新增 `skills` 子命令）
  - `zm_auto/services/registrar.py` / `zm_auto/services/user_info`（接入 site adapter）
- 无新增外部依赖；保持现有 CLI 默认行为不变。
- 测试：新增单元测试覆盖 tab 管理、录制增强、site adapter 注册、skill schema 生成、obstacle course 回归。
