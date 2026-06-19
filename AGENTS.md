# AGENTS.md — zm-auto 项目 AI 协作规则

> 本文件为 Codex / OpenCode / Copilot / Claude 等 AI agent 的本地项目规则。  
> 每次变更前请先读取本文件、README.md、`spec/` 以及对应 OpenSpec change 工件。

## 项目上下文

- **项目名**: zm-auto
- **定位**: 全自动账号注册 + API Key 获取的 Python 工具集
- **技术栈**: Python 3.x, `curl_cffi`, `requests`, `urllib3`, `playwright`（可选）, `SpeechRecognition`/`pydub`（可选）
- **核心脚本**:
  - `register.py` — 注册主流程 + CLI（纯 HTTP，curl_cffi）
  - `read_user_info.py` — 读取/导出已登录账号信息，支持自动创建 API Key
  - `mail_provider.py` — 7 个临时邮箱 provider 抽象
  - `captcha_solver.py` — 验证码求解器（2captcha / anticaptcha / Playwright / CDP）
  - `cdp_solver.py` — CDP 人工介入验证码处理
  - `check_account_status.py` — 账号状态检查
  - `sub2api_importer.py` — sub2api 兼容导出
- **配置与产物**:
  - `config.example.json` — 配置模板
  - `config.json` — 运行时配置（包含密钥，已 `.gitignore` 忽略）
  - `accounts.json` / `user_info.json` / `sub2api_export.json` — 运行输出（已忽略）
- **入口命令**:
  - `python register.py -n 1`
  - `python read_user_info.py`

## AI 协作纪律（Karpathy 行为纪律）

- **Think Before Coding**: 不确定需求、接口、权限、配置或调度语义时，先列出假设或提问，不静默猜测。
- **Simplicity First**: 只做当前规格范围内的最小可行改动，不增加未要求的抽象或扩展点。
- **Surgical Changes**: 只改当前变更直接相关文件；不顺手格式化、重构或删除无关代码。
- **Goal-Driven Execution**: 每个任务必须有成功标准和验证命令；未实际运行验证时不得声称验证通过。

## OpenSpec / Skills 门禁

### 变更生命周期 Skills（`.codex/skills/`）

| 阶段 | Skill | 用途 |
| --- | --- | --- |
| 创建 | `openspec-new-change` | 创建新变更工件 |
| 创建 | `openspec-propose` | 快速提案（轻量版） |
| 探索 | `openspec-explore` | 探索代码库、收集上下文 |
| 继续 | `openspec-continue-change` | 继续未完成变更 |
| 快速 | `openspec-ff-change` | 低风险小变更快速推进 |
| 实现前 | `openspec-superpowers-bridge` | 输出 Bridge Plan |
| 实现 | `openspec-apply-change` | 按 tasks.md 逐步实现 |
| 审查 | `spec-compliance-check` | Spec 合规审查 |
| 验证 | `openspec-verify-change` | 归档前一致性验证 |
| 同步 | `openspec-sync-specs` | 同步长期 specs |
| 完成 | `verification-before-completion` | 最终交付前验证 |
| 归档 | `openspec-archive-change` | 归档已完成变更 |
| 批量 | `openspec-bulk-archive-change` | 批量归档 |
| 接入 | `openspec-onboard` | 新项目接入引导 |

### 门禁规则

- 新需求、跨模块改动、验证码/邮箱 provider 新增、CLI 参数变化、配置文件结构变化、输出格式变化，必须先建立 `openspec/changes/<change-name>/`。
- 开始实现 OpenSpec change 前，必须输出 Bridge Plan，包含范围、非目标、高风险项、任务步骤、测试依据和停止条件。
- 实现后、代码审查前后或归档前，必须进行 Spec Compliance Check。
- 归档前必须使用或等价遵循 `openspec-verify-change`。
- 最终回复、PR、归档或合并前必须使用或等价遵循 `verification-before-completion`。
- 本项目验证以 `python -m py_compile <file>`、`python -m pytest tests/ -v`、`python <script> --help` 和真实 smoke 运行为主。
- 不要把本地 token、账号、密码、Cookie、运行时输出写入项目文件。

## 高风险检查矩阵

| 类型 | 关注点 | 推荐验证 |
| --- | --- | --- |
| 密钥 / 配置 | `config.json` 含 API Key、代理、邮箱 admin 密码 | 确认 `.gitignore` 已忽略 `config.json`；不提交真实密钥 |
| 验证码 | 2captcha / anticaptcha / browser / cdp 切换 | `python captcha_solver.py` 不报错（如 provider 配置正确） |
| 邮箱 provider | 临时邮箱 API 变化、域名失效 | 单个注册 `python register.py -n 1` 通过 |
| 目标站点 | `site_url`、邀请码、ctoken / sessionId 行为 | 抓取响应日志确认接口状态 |
| 输出文件 | `accounts.json` / `user_info.json` 格式变化 | 对比示例输出 |
| 第三方依赖 | `curl_cffi` / `playwright` 版本、系统 Chromium | `python -m py_compile *.py` |

## README / AGENTS 同步纪律

- 没有 `README.md` 时创建最小项目入口；已有时只增量合并。
- 每次变更完成前判断是否需要更新 `README.md`、`AGENTS.md`、`spec/` 或 `openspec/specs/`。
- 影响启动、构建、部署、测试、AI 开发纪律、高风险规则或验证命令的变更，必须同步对应入口文件。
- 不把单次变更过程写入 `README.md` 或 `AGENTS.md`；单次过程保留在 `openspec/changes/<change-name>/`。

## 常用命令

```bash
# 语法检查
python -m py_compile register.py read_user_info.py mail_provider.py captcha_solver.py cdp_solver.py check_account_status.py sub2api_importer.py

# 单元测试
python -m pytest tests/ -v

# 查看 CLI 帮助
python register.py --help
python read_user_info.py --help
```

## 多 AI 客户端协作模型

本项目支持多种 AI 客户端协作，通用规则以 `AGENTS.md` 为准，各客户端专用规则仅补充客户端特有的操作、上下文读取顺序和验证要求。任何客户端规则与 `AGENTS.md` 冲突时，以 `AGENTS.md` 为准。

| 客户端 | 规则文件 | 适用范围 |
| --- | --- | --- |
| Codex / OpenCode / 通用 Agent | `AGENTS.md` | 所有 AI 客户端的通用协作纪律、OpenSpec / Skills 门禁、高风险矩阵、验证策略 |
| Claude Code | `.claude/CLAUDE.md` | Claude Code 专用上下文，强调长上下文审查 `proposal.md/design.md/tasks.md` 的一致性 |
| Cursor | `.cursor/rules/rules.mdc` | Cursor 编辑器内规则，补充编码规范与 f-string 等细节 |
| Gemini | `GEMINI.md` | Gemini 项目规则，强调 OpenSpec 变更门禁与验证要求 |
| GitHub Copilot | `.github/copilot-instructions.md` | Copilot 生成代码时的纪律、变更流程与 `git status` 检查 |

### 协作约定

- 任何客户端开始工作前，都必须先读取 `AGENTS.md` 和 `spec/design.md`；之后根据自身客户端规则补充上下文。
- 新需求、跨模块改动、验证码/邮箱 provider 新增、CLI 参数变化、配置文件结构变化、输出格式变化，必须先在 `openspec/changes/<change-name>/` 建立变更工件。
- 实现前必须输出 Bridge Plan（范围、非目标、高风险项、任务步骤、验证命令、停止条件）。
- 实现后、审查前、归档前必须进行 Spec Compliance Check；归档前必须使用或等价遵循 `openspec-verify-change`；最终回复/PR/归档前必须使用或等价遵循 `verification-before-completion`。
- 不要把本地 token、账号、密码、Cookie、运行时输出写入任何项目文件。

### 客户端规则索引

- [`.claude/CLAUDE.md`](/Users/delphia/Documents/data/workspace/github/zm-auto/.claude/CLAUDE.md)
- [`.cursor/rules/rules.mdc`](/Users/delphia/Documents/data/workspace/github/zm-auto/.cursor/rules/rules.mdc)
- [`GEMINI.md`](/Users/delphia/Documents/data/workspace/github/zm-auto/GEMINI.md)
- [`.github/copilot-instructions.md`](/Users/delphia/Documents/data/workspace/github/zm-auto/.github/copilot-instructions.md)
