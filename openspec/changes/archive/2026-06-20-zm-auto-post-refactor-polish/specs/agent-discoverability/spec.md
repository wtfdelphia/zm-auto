# Agent Discoverability

## ADDED Requirements

### Requirement: 新增 SKILL.md

SHALL 新增 `.codex/zm-auto/SKILL.md`。

#### Scenario: SKILL.md 存在且内容完整

- 文件存在且包含项目描述、入口命令、安全约束。

### Requirement: SKILL.md 安全与依赖说明

SKILL.md SHALL 声明安全约束和依赖要求。

#### Scenario: SKILL.md 包含安全约束

- SKILL.md 包含 `config.json`、账号输出文件不提交的警告，以及 Python 版本/依赖说明。
