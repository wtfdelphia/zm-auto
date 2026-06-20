# CDP Session

## ADDED Requirements

### Requirement: 网络录制开关

`CDPSession` SHALL 支持启用/关闭网络请求录制。

#### Scenario: 启用和禁用录制

- 调用 `enable_recording()` 后，后续 Playwright page 请求会被记录。
- 调用 `disable_recording()` 后，不再记录新请求。

### Requirement: 录制数据读取与清空

录制数据 SHALL 可通过 `get_recording()` 读取，`clear_recording()` SHALL 清空录制数据。

#### Scenario: 读取和清空录制记录

- `get_recording()` 返回列表，包含 request/response 条目。
- `clear_recording()` 后 `get_recording()` 返回空列表。

### Requirement: 默认不录制

不开启录制时 SHALL 不影响性能。

#### Scenario: 默认录制列表为空

- 默认 `CDPSession()` 的录制列表为空，未附加事件监听。
