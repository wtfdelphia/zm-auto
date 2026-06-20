# CLI Interface

## ADDED Requirements

### Requirement: doctor 紧凑输出

`python -m zm_auto doctor --compact` SHALL 输出单行关键状态，且 SHALL 不破坏默认 text 模式。

#### Scenario: --compact 参数可用

- `python -m zm_auto doctor --help` 显示 `--compact` 参数。
- `python -m zm_auto doctor --compact` 返回非空单行输出。

### Requirement: doctor 增强信息

doctor 输出 SHALL 包含配置加载状态、provider 数量、CDP 可达性、依赖版本摘要。

#### Scenario: JSON 输出包含增强字段

- `python -m zm_auto doctor --format json` 包含 `dependencies`、`mail_providers`、`cdp_reachable` 字段。
