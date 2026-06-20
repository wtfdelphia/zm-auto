# cdp-session Specification

## Purpose

定义 `CDPSession` 的生命周期管理、网络请求录制、多 tab 切换以及增强录制数据的能力，为注册与用户信息读取流程提供稳定的 CDP 抽象。

## Requirements

### Requirement: 网络录制开关

`CDPSession` SHALL 支持启用/关闭网络请求录制。

#### Scenario: 启用和禁用录制

- 调用 `enable_recording()` 后，后续 Playwright page 请求会被记录。
- 调用 `disable_recording()` 后，不再记录新请求。

### Requirement: 录制数据读取、清空与 HAR 导出

录制数据 SHALL 可通过 `get_recording()` 读取，`clear_recording()` SHALL 清空录制数据，`export_har()` SHALL 将录制数据导出为 HAR 1.2 JSON。

#### Scenario: 读取、清空与导出 HAR

- `get_recording()` 返回列表，包含 request/response 条目。
- `clear_recording()` 后 `get_recording()` 返回空列表。
- `export_har()` 返回符合 HAR 1.2 的 JSON 字符串。

### Requirement: 默认不录制

不开启录制时 SHALL 不影响性能。

#### Scenario: 默认录制列表为空

- 默认 `CDPSession()` 的录制列表为空，未附加事件监听。

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

### Requirement: 录制条目包含单调递增 seq

每个录制事件 SHALL 包含全局单调递增的 `seq` 字段。

#### Scenario: 事件按 seq 排序

- **WHEN** 连续发生 request 和 response
- **THEN** `seq` 严格递增
- **AND** seq 为整数

### Requirement: request 与 response 配对

属于同一 HTTP 请求的 request 和 response 事件 SHALL 具有相同的 `request_id`。

#### Scenario: 配对成功

- **WHEN** 一个 GET 请求返回 200
- **THEN** recording 中存在 request 和 response 两个条目
- **AND** 它们的 `request_id` 相同

### Requirement: 支持 trigger 因果链

`CDPSession` SHALL 提供 `mark_trigger(name)` 方法，在录制中插入 trigger 条目；后续 request/response 可携带 `trigger_seq` 指向最近的 trigger。

#### Scenario: 标记 trigger

- **WHEN** 调用 `session.mark_trigger("click_submit")`
- **THEN** recording 中出现一条 type=trigger 的条目
- **AND** 后续网络请求包含 `trigger_seq` 字段
### Requirement: CDPSession 支持注入 stealth 脚本

`CDPSession` SHALL 提供 `add_stealth_scripts(page)` 方法，通过 `Page.addScriptToEvaluateOnNewDocument` 注入反检测脚本，不影响未调用时的默认行为。

#### Scenario: 启用 stealth 后页面检测点被隐藏

- **WHEN** 调用 `add_stealth_scripts(page)` 并导航
- **THEN** `navigator.webdriver` 为 `undefined`
- **AND** `window.chrome` 存在且不为空对象
