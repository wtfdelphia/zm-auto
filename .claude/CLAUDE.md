# CLAUDE.md — Claude Code 项目规则

> 本文件为 Claude Code 专用上下文。规则与 `AGENTS.md` 冲突时，以 `AGENTS.md` 为准，本文件仅补充 Claude 特有操作。

## 项目上下文

- 项目名: zm-auto
- 技术栈: Python 3.x, curl_cffi, requests, urllib3, 可选 playwright
- 入口: `register.py`, `read_user_info.py`
- AI 通用规则: `AGENTS.md`
- 长期事实: `spec/`
- OpenSpec 变更: `openspec/changes/<change-name>/`

## 协作纪律

- 读取本文件后，仍需先读 `AGENTS.md` 和 `spec/design.md`。
- 每次变更必须能够追溯到 OpenSpec change 或明确的 hotfix 理由。
- 不确定时列出假设，不静默猜测。

## 常用命令

```bash
# 语法检查
python3 -m py_compile register.py read_user_info.py mail_provider.py captcha_solver.py cdp_solver.py check_account_status.py sub2api_importer.py

# 单元测试
python3 -m pytest tests/ -v

# CLI 帮助
python3 register.py --help
python3 read_user_info.py --help

# OpenSpec 校验
openspec validate --all
```

## Claude Code Commands

本项目提供以下 Claude Code 自定义命令（`.claude/commands/`）：

| 命令 | 用途 |
|------|------|
| `/opsx:new` | 创建新的 OpenSpec 变更 |
| `/opsx:apply` | 按 tasks.md 逐步实现 |
| `/opsx:verify` | 归档前验证实现与工件一致性 |
| `/opsx:archive` | 归档已完成变更 |

## Claude Code Skills

本项目提供以下 Claude Code 自定义 Skills（`.claude/skills/`）：

| Skill | 用途 |
|-------|------|
| `openspec-workflow` | OpenSpec 完整变更生命周期编排 |
| `spec-compliance` | Spec 合规审查 |

## Claude 特有提示

- 使用长上下文审查复杂 change 时，优先核对 `proposal.md`、`design.md`、`tasks.md` 之间的一致性。
- 不要修改 `.claude/settings.local.json`，该文件已被 `.gitignore` 忽略。
- 所有 OpenSpec 工作流命令和 skills 与 `.codex/skills/` 中的项目内 skills 等价，确保不同客户端行为一致。
