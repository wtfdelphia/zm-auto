# OpenSpec Workflow Skill

## 触发条件

当用户要求创建新功能、跨模块修改、高风险修复时，或提及 `/opsx:new`、`/opsx:apply`、`/opsx:verify`、`/opsx:archive` 时。

## 工作流

本 skill 编排 zm-auto 项目的完整 OpenSpec 变更生命周期，与 `.codex/skills/` 中的项目内 skills 等价。

### 阶段 1: 创建变更

1. 读取 `AGENTS.md`、`spec/design.md`、`openspec/project.md`
2. 运行 `openspec new change "<name>"`
3. 按 spec-driven schema 创建 proposal.md、design.md、tasks.md
4. 如涉及 capability 变更，创建 `specs/<capability>/spec.md` delta spec

### 阶段 2: Bridge Plan

实现前必须输出 Bridge Plan，包含：
- 范围、非目标、关键决策
- 高风险项（配置/密钥、验证码 provider、CLI/输出契约、目标站点行为）
- CodeGraph / rg 影响面证据
- 任务到执行步骤映射
- 必跑验证命令
- 停止条件

### 阶段 3: 实现

1. 读取 `openspec instructions apply --change "<name>" --json`
2. 读取所有 contextFiles
3. 按 tasks.md 逐项实现，保持改动最小化
4. 每完成一项立即勾选 `- [x]`

### 阶段 4: 合规审查

运行 `spec-compliance-check`，审查维度：
- Scope: 是否超出范围
- Design: 是否遵守 design.md
- Scenarios: 每个 Requirement 是否有实现证据
- Project Rules: 是否遵守 AGENTS.md 和 spec/
- Verification: 验证命令是否真实运行
- README/AGENTS Sync: 入口文件是否需要更新

### 阶段 5: 验证与归档

1. `openspec-verify-change`: 验证 Completeness、Correctness、Coherence
2. `verification-before-completion`: 最终验证门禁
3. README/AGENTS/spec 同步判断
4. `openspec archive <name>`

## 验证命令

```bash
python -m py_compile register.py read_user_info.py mail_provider.py captcha_solver.py cdp_solver.py check_account_status.py sub2api_importer.py
python -m pytest tests/ -v
python register.py --help
python read_user_info.py --help
openspec validate --all
```
