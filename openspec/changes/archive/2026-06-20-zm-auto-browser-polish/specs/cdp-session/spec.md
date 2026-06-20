# cdp-session Delta Specification

## Purpose

在已有 CDP 网络录制能力基础上扩展 HAR 导出与 stealth 注入能力。

## MODIFIED Requirements

### Requirement: 网络录制数据读取与清空

录制数据 SHALL 可通过 `get_recording()` 读取，`clear_recording()` SHALL 清空录制数据，并新增 `export_har()` 方法将录制数据导出为 HAR 1.2 JSON。

#### Scenario: 读取、清空与导出 HAR

- `get_recording()` 返回列表，包含 request/response 条目。
- `clear_recording()` 后 `get_recording()` 返回空列表。
- `export_har()` 返回符合 HAR 1.2 的 JSON 字符串。

### Requirement: CDPSession 支持注入 stealth 脚本

`CDPSession` SHALL 提供 `add_stealth_scripts(page)` 方法，为 page 注入反检测脚本，且不影响未调用时的默认行为。

#### Scenario: 启用 stealth 后页面检测点被隐藏

- **WHEN** 调用 `add_stealth_scripts(page)` 并导航
- **THEN** `navigator.webdriver` 为 `undefined`
- **AND** `window.chrome` 存在且不为空对象
