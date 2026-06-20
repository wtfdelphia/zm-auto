# agent-skills-schema Specification

## Purpose

从 CLI 命令注册表自动生成 AI Agent 可用的 skill schema，降低 Agent 调用 CLI 的歧义。

## Requirements

### Requirement: registry_json_schema 输出 OpenAI function schema

`zm_auto.cli.commands.registry_json_schema()` SHALL 返回每个命令的 JSON Schema，包含 `description`、`properties`、`required`。

#### Scenario: register 命令 schema

- **WHEN** 调用 `registry_json_schema()`
- **THEN** `register` 项包含 `total`、`threads`、`proxy`、`yes` 字段
- **AND** 必填参数标记为 `required`

### Requirement: CLI 提供 skills 子命令

`python -m zm_auto skills` SHALL 输出上述 JSON schema，支持 `--format json`（默认）和 `--format compact`。

#### Scenario: skills 命令输出合法 JSON

- **WHEN** 执行 `python -m zm_auto skills`
- **THEN** 输出合法 JSON
- **AND** 顶层键包含 `register`、`user-info`、`account-status`、`doctor`、`skills`

