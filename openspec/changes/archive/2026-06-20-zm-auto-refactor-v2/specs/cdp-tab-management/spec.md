# cdp-tab-management Specification

## Purpose

让 `CDPSession` 支持多 tab 短 ID 管理，每个 tab 拥有独立的生命周期和事件隔离，避免单 page 模型在复杂注册流程中的限制。

## ADDED Requirements

### Requirement: CDPSession 支持创建与切换 tab

`CDPSession` SHALL 提供 `new_tab()` 方法创建新 tab，并返回短 ID；提供 `switch_tab(tab_id)` 切换到指定 tab；提供 `close_tab(tab_id)` 关闭指定 tab。

#### Scenario: 创建新 tab

- **WHEN** 调用 `session.new_tab()`
- **THEN** 返回 4 位十六进制短 ID
- **AND** `session.tabs` 中包含该短 ID

#### Scenario: 切换 tab

- **WHEN** 存在多个 tab 时调用 `session.switch_tab(tab_id)`
- **THEN** `session.page` 返回对应 tab 的 page

### Requirement: 每个 tab 的录制相互隔离

每个 tab 的录制 SHALL 相互隔离，当前活跃 tab 的录制不影响其他 tab。

#### Scenario: tab 之间录制隔离

- **WHEN** tab A 和 tab B 分别产生网络请求
- **THEN** 在 tab A 活跃时 `get_recording()` 只返回 tab A 的请求
- **AND** `clear_recording()` 只清空当前活跃 tab 的录制

### Requirement: 关闭 session 时关闭所有 tab

关闭 `CDPSession` 时 SHALL 关闭所有已打开 tab 并释放 browser/playwright 资源。

#### Scenario: 上下文管理器退出

- **WHEN** `CDPSession` 作为上下文管理器退出
- **THEN** 所有已打开 tab 的 page 都被关闭
- **AND** browser/playwright 资源被释放
