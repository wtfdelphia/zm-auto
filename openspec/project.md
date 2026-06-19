# zm-auto OpenSpec Project

## Project Facts

- 项目名: zm-auto
- 定位: 全自动账号注册 + API Key 获取的 Python 工具集
- 技术栈: Python 3.x
- 主入口: `register.py`, `read_user_info.py`
- 通用规则: `AGENTS.md`
- 设计事实: `spec/design.md`

## 事实源分层

| 层级 | 路径 | 读者 | 用途 |
| --- | --- | --- | --- |
| 项目事实 | `spec/` | 人类 + AI | 长期需求、架构设计、目录结构 |
| Capability Specs | `openspec/specs/` | OpenSpec 工具 | 可验证的 capability 规格，供 `openspec validate` 使用 |
| 单次变更 | `openspec/changes/` | 当前变更参与者 | proposal、design、tasks、验证证据 |

`spec/` 与 `openspec/specs/` 描述同一组能力，但前者是面向人类的叙述性文档，后者是面向工具的格式化规格。两者内容应保持同步。

## Capability Specs

- `openspec/specs/account-registration/spec.md` — 账号注册流程
- `openspec/specs/captcha-provider/spec.md` — 验证码求解接口
- `openspec/specs/mail-provider/spec.md` — 临时邮箱 provider 抽象

## Skills 清单

| Skill | 阶段 |
| --- | --- |
| `openspec-new-change` | 创建新变更 |
| `openspec-propose` | 快速提案 |
| `openspec-explore` | 代码探索 |
| `openspec-continue-change` | 继续变更 |
| `openspec-ff-change` | 快速推进 |
| `openspec-superpowers-bridge` | Bridge Plan |
| `openspec-apply-change` | 逐步实现 |
| `spec-compliance-check` | 合规审查 |
| `openspec-verify-change` | 一致性验证 |
| `openspec-sync-specs` | 同步 specs |
| `verification-before-completion` | 交付验证 |
| `openspec-archive-change` | 归档 |
| `openspec-bulk-archive-change` | 批量归档 |
| `openspec-onboard` | 项目接入 |

## Change Workflow

1. 新需求、跨模块改动、高风险修复：使用 `openspec-new-change` 或 `openspec-propose` 创建 `openspec/changes/<name>/`。
2. 探索上下文：使用 `openspec-explore` 收集代码影响面。
3. 继续已有变更：使用 `openspec-continue-change`。
4. 小变更快速推进：使用 `openspec-ff-change`（仅限低风险）。
5. 开始实现前：使用 `openspec-superpowers-bridge` 输出 Bridge Plan。
6. 实现：使用 `openspec-apply-change` 按 tasks.md 逐步实现。
7. 实现后：使用 `spec-compliance-check`。
8. 归档前：使用 `openspec-verify-change`。
9. 同步长期 specs：使用 `openspec-sync-specs`。
10. 最终交付前：使用 `verification-before-completion`。
11. 归档：使用 `openspec-archive-change` 或 `openspec-bulk-archive-change`。

## Verification Baseline

- `python -m py_compile register.py read_user_info.py mail_provider.py captcha_solver.py cdp_solver.py check_account_status.py sub2api_importer.py`
- `python -m pytest tests/ -v`
- `python register.py --help`
- `python read_user_info.py --help`
- `openspec validate --all`
