## Context

`refactor-zm-auto-package` 已经把脚本重构成 `zm_auto/` 包，`zm-auto-browser-polish` 补齐了 CDP 录制导出、stealth 注入、错误重试和 doctor JSON 输出。当前 `CDPSession` 只管理单一 page，录制数据只有扁平的 request/response 事件，且 zenmux 站点逻辑硬编码在 service 层。本次设计通过借鉴 `bb-browser` 的 tab/事件隔离、`obscura` 的 obstacle course 回归，以及 `browser-act/skills` 的 Agent 自描述能力，把这些局部能力提升到架构层。

## Goals / Non-Goals

**Goals:**
- `CDPSession` 支持多 tab 短 ID 管理与生命周期隔离。
- 录制数据支持 seq、请求/响应配对、trigger 因果链。
- 站点逻辑抽象为可插拔 adapter，通过 `__subclasses__()` 自动发现。
- CLI 命令注册表可导出 AI Agent 可用的 skill schema。
- 新增离线 fixtures 回归套件（obstacle course），验证注册/CDP 主路径。

**Non-Goals:**
- 不引入新的外部依赖（如 playwright-stealth、Flask 等；obstacle course 用标准库）。
- 不替换现有 provider 实现，仅在 CDP/CLI 层扩展。
- 不实现远程 hub/WebRTC（超出当前架构）。
- 不改动现有 CLI 默认行为。

## Decisions

1. **Tab 管理内聚在 CDPSession 内**：不单独创建 `TabManager`，而是让 `CDPSession` 维护 `{short_id: _Tab}` 字典。这样 `new_page()` 升级成 `new_tab()`，旧 `page` 属性保留为当前活跃 tab，兼容现有代码。
2. **短 ID 用 4 位十六进制**：与 bb-browser 一致，足够短且冲突概率低；冲突时自增重试。
3. **录制数据使用 dataclass 而非 dict**：新增 `zm_auto/cdp/recording.py` 定义 `RecordingEntry`、`RequestEntry`、`ResponseEntry`，便于类型检查和 schema 稳定。
4. **Site adapter 接口最小化**：`BaseSiteAdapter` 只声明 `name`、`site_url` 和站点路径抽象方法（`user_info_path()`、`api_key_list_path()`、`api_key_page_path()`、`register_endpoints()`）。具体 adapter 决定如何构造 HTTP/CDP 请求。
5. **Skill schema 生成走注册表**：`registry_json_schema()` 已经从 `COMMANDS` 生成，本次只需补全参数类型映射，并新增 `skills` 子命令输出。
6. **Obstacle course 用标准库 http.server**：避免新增依赖；测试在随机端口起服务，测试结束关闭。

## Risks / Trade-offs

- **多 tab 引入状态复杂度**：需要确保 `close()` 时关闭所有 tab，避免资源泄漏。→ `__exit__` 中遍历 `_tabs` 关闭。
- **录制配对可能丢失**：如果 response 事件在 request 之前到达（理论上不应发生），配对失败。→ 未配对条目单独保留，不影响整体 HAR 导出。
- **Site adapter 增加一层抽象**：短期对单一 zenmux 站点是过度设计。→ 但为后续多站点支持留下扩展点，且本次改动小。
- **Obstacle course fixtures 无法覆盖真实反爬**：只能验证主路径，不能替代真实站点 smoke。→ 明确 fixtures 仅作为回归第一道防线。

## Migration Plan

- 本次变更新增模块并扩展 API，不破坏现有调用。
- 现有 `CDPSession.page` 仍返回当前活跃 page。
- `services/registrar.py` 和 `services/user_info` 逐步接入 `SiteAdapter`，但保留原有逻辑作为 fallback。

## Open Questions

- 是否需要为 stealth 脚本提供按站点配置？（当前不实现，保留扩展点。）
- HAR 导出是否需要支持过滤域名或 URL 模式？（当前不实现，可在后续变更中补充。）
