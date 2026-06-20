# cdp-har-export Specification

## Purpose

提供将 `CDPSession` 网络录制数据导出为 HAR 1.2 格式的方法，便于在浏览器自动化流程中进行离线调试、性能分析与合规审计。

## Requirements

### Requirement: CDPSession 支持导出 HAR

`CDPSession` SHALL 提供 `export_har()` 方法，将已录制的 request/response 条目转换为 HAR 1.2 JSON 字符串。

#### Scenario: 空录制导出空 HAR

- **WHEN** 录制列表为空
- **THEN** `export_har()` 返回包含空 `entries` 数组的有效 HAR JSON

#### Scenario: 录制条目导出为 HAR 条目

- **WHEN** 录制列表中包含一条 GET 200 的 request/response
- **THEN** `export_har()` 返回的 JSON 中 `entries` 长度为 1
- **AND** 该条目包含 `request.method`、`request.url`、`response.status`、`response.content` 字段

### Requirement: HAR 时间戳与耗时字段

每个 HAR 条目 SHALL 包含 `startedDateTime`、`time`、`timings` 字段，时间格式符合 ISO 8601，耗时单位为毫秒。

#### Scenario: 时间字段格式正确

- **WHEN** 调用 `export_har()`
- **THEN** 每个 entry 的 `startedDateTime` 以 `Z` 结尾
- **AND** `time` 为非负整数
- **AND** `timings` 包含 `send`、`wait`、`receive`

### Requirement: HAR 输出可序列化

`export_har()` 返回的结果 SHALL 可直接被 `json.dumps` / `json.loads` 往返，不抛出异常。

#### Scenario: JSON 往返

- **WHEN** 将 `export_har()` 结果写入文件后再读取
- **THEN** 读取结果与原 JSON 一致
