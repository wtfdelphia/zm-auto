# cdp-recording-enhanced Specification

## Purpose

增强 `CDPSession` 的录制数据，使其支持单调序列号、请求/响应配对和因果链，便于离线调试和 HAR 分析。

## ADDED Requirements

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
