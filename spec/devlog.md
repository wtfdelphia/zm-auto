# 开发日志

## 2026-06-19 — AI 辅助开发工程化接入

### 完成项

- 建立三层事实资产：`spec/requirements.md`、`spec/design.md`、`spec/structure.md`
- 创建 `AGENTS.md` 作为通用 AI agent 规则，含 OpenSpec 门禁、高风险矩阵、验证策略
- 创建 5 个客户端规则文件：`.claude/CLAUDE.md`、`.cursor/rules/rules.mdc`、`GEMINI.md`、`.github/copilot-instructions.md`
- 接入 OpenSpec：初始化 `openspec/`，建立 3 个 capability specs（account-registration、captcha-provider、mail-provider）
- 接入 CodeGraph：索引代码图谱，配置 MCP
- 安装 14 个项目内 Skills（`.codex/skills/`），覆盖完整变更生命周期
- 接入 MCP 服务：fetch、memory、playwright、codegraph
- 创建 `docs/tooling-sources.md` 记录工具来源和版本
- 创建 `docs/AI 辅助开发工程化落地白皮书.md`
- 编写 `README.md` 包含 SpecCoding 入口

### 已知缺口

- `openspec/changes/` 无活跃变更，OpenSpec 全链路从未实战运行
- 测试覆盖率仍有提升空间，核心模块（`register`、`captcha_solver`、`mail_provider`、`sub2api_importer`）已覆盖
- `docs/auto.js` 定位不当（非文档，已 `.gitignore`）

### 工具版本

| 工具 | 版本 | 核验日期 |
| --- | --- | --- |
| OpenSpec | 1.4.0 | 2026-06-19 |
| CodeGraph | 0.9.8 | 2026-06-19 |
| ripgrep | 15.1.0 | 2026-06-19 |
| Node.js | v24.14.1 | 2026-06-19 |
| Python | 3.12.13 | 2026-06-19 |
| pytest | 9.1.1 | 2026-06-19 |

## 2026-06-19 — 工程化落地审核与修复

### 修复项

- 修正 `tooling-sources.md` 中 Python 版本（3.9.6 → 3.12.13）
- 修正 `README.md` 中"无单元测试框架"错误描述
- 补充 `README.md` SpecCoding 完整入口（含常用命令）
- `openspec update` 自动新增 6 个 skill：`openspec-apply-change`、`openspec-bulk-archive-change`、`openspec-explore`、`openspec-onboard`、`openspec-propose`、`openspec-sync-specs`
- 更新 `AGENTS.md` 补充完整 Skills 清单（14 个）
- 更新 `openspec/project.md` 补充事实源分层说明和 Skills 清单
- 创建 `spec/devlog.md`（本文件）
