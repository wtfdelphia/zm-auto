# Design

## 架构风格

- 单进程多线程 Python 脚本集合，无服务框架。
- 注册流程以 `register.py` 为入口，按顺序调用邮箱、验证码、HTTP 请求模块。
- 配置外置：运行时依赖 `config.json`，模板为 `config.example.json`。

## 模块边界

```
register.py  ──>  mail_provider.py  ──>  临时邮箱 API
          │
          ├──>  captcha_solver.py  ──>  2captcha / anticaptcha / Playwright / CDP
          │
          └──>  read_user_info.py / check_account_status.py / sub2api_importer.py
```

- `mail_provider.py`: 统一邮箱 provider 接口，隐藏不同 API 差异。
- `captcha_solver.py`: 统一验证码求解接口，根据 `captcha.provider` 分发。
- `cdp_solver.py`: 连接远程 Chrome，辅助完成人工介入式验证码。
- `register.py`: 编排注册流程、CLI 参数解析、并发控制、结果持久化。
- `read_user_info.py`: 读取已有登录态，导出用户信息，按需创建 API Key。

## 接口 / 数据

- 目标站点接口通过 `config.json` 的 `site_url` 拼接。
- 统一返回 `Result<T>` 的目标站点接口由 `register.py` 解析。
- 输出 JSON 格式：`accounts.json` 与 `user_info.json`。

## 权限 / 安全

- 所有密钥、密码、代理、邀请码只存于 `config.json`，项目仓库不保留。
- `config.example.json` 作为模板，不含真实密钥。
- 运行时输出文件（`accounts.json` 等）同样不提交。

## 异常路径

- 邮箱验证码获取超时：按 `wait_timeout` 重试，超时退出。
- 验证码求解失败：按 provider 重试或抛出异常。
- 目标站点返回白名单/等待列表：根据 `on_waitlist` 配置处理（`abort` 或继续）。
- API Key 创建失败：记录失败账号，不阻塞其他并发任务。

## 回滚策略

- 无数据库事务。失败账号状态通过日志与 `accounts.json` 记录。
- 需要清理时，可删除 `accounts.json` / `user_info.json` 重新运行。

## 验证策略

- 静态检查：`python -m py_compile *.py`
- CLI 帮助：`python register.py --help`、`python read_user_info.py --help`
- 冒烟验证：`python register.py -n 1`（需配置正确的 `config.json`）
- 配置模板校验：确保 `config.example.json` 与 `config.json` 字段一致

## 多 AI 客户端协作模型

为支持不同 AI 客户端（Codex、OpenCode、Claude Code、Cursor、GitHub Copilot、Gemini）在同一项目中协作，项目采用“通用规则 + 客户端补充规则”两层模型：

1. **通用规则**：`AGENTS.md` 定义所有 AI 客户端必须遵守的项目上下文、协作纪律、OpenSpec / Skills 门禁、高风险矩阵和验证策略。
2. **客户端补充规则**：各客户端专用规则文件仅补充该客户端的读取顺序、上下文习惯和验证细节；与 `AGENTS.md` 冲突时以 `AGENTS.md` 为准。

### 客户端规则文件

| 客户端 | 文件 | 说明 |
| --- | --- | --- |
| 通用 / Codex / OpenCode | `AGENTS.md` | 通用协作纪律、OpenSpec / Skills 门禁、高风险矩阵、README/AGENTS 同步纪律 |
| Claude Code | `.claude/CLAUDE.md` | 先读 `AGENTS.md` 和 `spec/design.md`；长上下文审查时核对 `proposal.md`、`design.md`、`tasks.md` 的一致性 |
| Cursor | `.cursor/rules/rules.mdc` | 编辑器内规则，补充 Python 编码规范、f-string 嵌套引号检查、密钥不硬编码 |
| Gemini | `GEMINI.md` | 项目上下文、OpenSpec 变更门禁、验证要求（静态检查、CLI 帮助、冒烟） |
| GitHub Copilot | `.github/copilot-instructions.md` | 生成代码纪律、最小改动、OpenSpec 变更流程、完成前检查 `git status --short` |

### 协作流程

- 任何客户端开始工作前，都必须先读取 `AGENTS.md` 和 `spec/design.md`。
- 新需求、跨模块改动、高风险修复必须先建立 `openspec/changes/<change-name>/`。
- 实现前输出 Bridge Plan；实现后更新 `tasks.md` 并运行验证；归档前进行 Spec Compliance Check 和 `openspec-verify-change`；最终回复前进行 `verification-before-completion`。
- 所有客户端共享同一套项目内 Skills（`.codex/skills/`），用于 OpenSpec 变更的创建、审查、验证与归档。
