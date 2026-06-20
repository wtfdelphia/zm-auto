# cli-interface Delta Specification

## Purpose

扩展 `doctor` 命令输出格式，支持机器可读的 JSON。

## MODIFIED Requirements

### Requirement: doctor 增强信息

doctor 输出 SHALL 包含配置加载状态、provider 数量、CDP 可达性、依赖版本摘要，并支持 `--format json` 以 JSON 格式输出。

#### Scenario: doctor JSON 输出

- **WHEN** 执行 `python -m zm_auto doctor --format json`
- **THEN** 输出为合法 JSON
- **AND** 包含 `dependencies`、`mail_providers`、`cdp_reachable` 字段
- **AND** 包含 `ok` 布尔字段表示整体健康状态

#### Scenario: --format 默认值为 text

- **WHEN** 执行 `python -m zm_auto doctor`（不带 `--format`）
- **THEN** 仍使用原有文本输出格式
