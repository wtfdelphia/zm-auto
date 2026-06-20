# cli-interface Specification

## Purpose

定义 zm-auto 命令行接口的整体结构、子命令注册方式和通用行为约束，使其既可人工使用，也便于 AI Agent 消费。

## Requirements

### Requirement: click 统一 CLI

系统 SHALL 使用 click 提供 `python -m zm_auto <subcommand>` 统一 CLI 入口，包含 `register`、`user-info`、`account-status`、`doctor` 和 `skills` 五个子命令。

#### Scenario: 查看帮助

- **WHEN** 执行 `python -m zm_auto --help`
- **THEN** 显示所有子命令列表及描述

#### Scenario: register 子命令

- **WHEN** 执行 `python -m zm_auto register --help`
- **THEN** 显示 `-n`、`-t`、`--proxy`、`--yes` 参数说明

#### Scenario: user-info 子命令

- **WHEN** 执行 `python -m zm_auto user-info --help`
- **THEN** 显示 `--cdp-url`、`-o`、`--export-sub2api`、`--create-key`、`--yes` 等参数说明

#### Scenario: doctor 子命令

- **WHEN** 执行 `python -m zm_auto doctor --help`
- **THEN** 显示 doctor 子命令说明
- **AND** 执行 `python -m zm_auto doctor` 时输出配置状态、可用 provider 列表、可用 captcha provider 列表、CDP 可达性、输出文件路径

#### Scenario: skills 子命令

- **WHEN** 执行 `python -m zm_auto skills --help`
- **THEN** 显示 `--format json|compact` 参数说明
- **AND** 执行 `python -m zm_auto skills` 时输出合法 JSON，包含所有命令的 schema

### Requirement: 命令统一注册表

系统 SHALL 在 `zm_auto/cli/commands.py` 中集中定义所有子命令的元数据（名称、分组、描述、参数、handler 路径），click 子命令从该注册表生成。

#### Scenario: 注册表是单一定义源

- **WHEN** 检查 `zm_auto/cli/commands.py`
- **THEN** 存在 `COMMANDS` 列表，包含 register / user-info / account-status / doctor / skills 的元数据
- **AND** `zm_auto/cli/__init__.py` 从 `COMMANDS` 动态注册 click 子命令
- **AND** 新增子命令时只需修改 `commands.py` 和对应 handler 文件

#### Scenario: 帮助信息从注册表生成

- **WHEN** 执行 `python -m zm_auto --help`
- **THEN** 显示的子命令名称和描述与 `COMMANDS` 中定义一致

### Requirement: verbose 日志控制

系统 SHALL 通过 `--verbose` / `-v` 全局参数控制日志级别。

#### Scenario: 默认日志级别

- **WHEN** 执行 `python -m zm_auto register -n 1`（不带 `-v`）
- **THEN** 仅显示 INFO 及以上级别日志

#### Scenario: verbose 模式

- **WHEN** 执行 `python -m zm_auto -v register -n 1`
- **THEN** 显示 DEBUG 级别日志

### Requirement: 无裸 print 调试输出

系统 SHALL 使用 `logging` 模块输出所有日志，不存在 `print(DEBUG...)` 调试语句。

#### Scenario: 代码中无 DEBUG print

- **WHEN** 搜索 `zm_auto/` 下所有 `.py` 文件中的 `print` 语句
- **THEN** 不存在包含 `DEBUG` 字样的 print 调用
- **AND** 所有输出通过 `logging.getLogger(__name__)` 输出

### Requirement: CLI 错误输出带 hint

系统 SHALL 在 CLI 捕获 `ZMError` 时输出 `message` 和 `hint`。

#### Scenario: 错误提示

- **WHEN** 某个子命令因配置缺失抛出 `ZMError("missing api key", hint="set captcha.api_key or use provider='browser'")`
- **THEN** 终端输出 `Error: missing api key` 和 `Hint: set captcha.api_key or use provider='browser'`
- **AND** 退出码非 0

### Requirement: 敏感操作确认门控

系统 SHALL 对付费验证码调用、API Key 创建、CDP 人工模式默认进行交互式确认，并提供 `--yes`/`-y` 参数跳过。

#### Scenario: 默认确认

- **WHEN** 执行 `python -m zm_auto register -n 1` 且 `captcha.provider` 为 `2captcha`
- **THEN** 提示用户确认是否继续
- **AND** 用户未确认时不会调用付费验证码 API

#### Scenario: 跳过确认

- **WHEN** 执行 `python -m zm_auto register -n 1 --yes`
- **THEN** 不提示确认，直接执行

### Requirement: doctor 紧凑输出

`python -m zm_auto doctor --compact` SHALL 输出单行关键状态，且 SHALL 不破坏默认 text 模式。

#### Scenario: --compact 参数可用

- `python -m zm_auto doctor --help` 显示 `--compact` 参数。
- `python -m zm_auto doctor --compact` 返回非空单行输出。

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

### Requirement: skills schema 输出

`python -m zm_auto skills` SHALL 输出 AI Agent 可用的命令注册表 JSON Schema，支持 `--format json`（默认）和 `--format compact`。

#### Scenario: skills 输出合法 JSON

- **WHEN** 执行 `python -m zm_auto skills`
- **THEN** 输出合法 JSON
- **AND** 顶层键包含 `register`、`user-info`、`account-status`、`doctor`、`skills`

