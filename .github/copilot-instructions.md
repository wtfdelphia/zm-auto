# GitHub Copilot Instructions — zm-auto

## 项目概述

zm-auto 是一个 Python 工具集，用于自动化账号注册和 API Key 获取。

- 入口: `register.py`, `read_user_info.py`
- AI 通用规则: `AGENTS.md`
- 架构事实: `spec/design.md`
- OpenSpec 变更目录: `openspec/changes/<change-name>/`

## 生成代码时的纪律

- 只做当前任务的最小改动。
- 不增加未要求的抽象或扩展点。
- 保持与现有代码风格一致。
- 密钥、密码、Cookie 不得硬编码。

## 变更流程

- 新功能、跨模块改动、高风险修复：先建 OpenSpec change。
- 实现前输出 Bridge Plan（范围、非目标、验证命令）。
- 实现后更新 `tasks.md` 并运行验证。
- 完成前检查 `git status --short`。
