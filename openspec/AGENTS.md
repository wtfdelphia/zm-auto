# AGENTS.md — OpenSpec 工具上下文

> 本文件为 OpenSpec CLI 工具在本项目中的使用规则。
> 与项目根 `AGENTS.md` 冲突时，以项目根 `AGENTS.md` 为准。

## 项目事实源

OpenSpec 在本项目中管理三层事实：

| 层级 | 路径 | 读者 | 用途 |
|------|------|------|------|
| 项目事实 | `spec/` | 人类 + AI | 长期需求、架构设计、目录结构 |
| Capability Specs | `openspec/specs/` | OpenSpec 工具 | 可验证的 capability 规格 |
| 单次变更 | `openspec/changes/` | 当前变更参与者 | proposal、design、tasks、验证证据 |

## OpenSpec 版本

- 当前版本: 1.4.0
- 核验日期: 2026-06-19
- 工具来源: `https://github.com/Fission-AI/OpenSpec`

## 变更生命周期

每次变更必须走完以下闭环：

1. **创建变更**: `openspec new change "<name>"`，按 spec-driven schema 创建工件
2. **Bridge Plan**: 实现前使用 `openspec-superpowers-bridge` 输出 Bridge Plan
3. **实现**: 按 `tasks.md` 小步实现，每完成一项勾选 `- [x]`
4. **合规审查**: 使用 `spec-compliance-check` 审查六维度
5. **一致性验证**: 使用 `openspec-verify-change` 验证 Completeness、Correctness、Coherence
6. **最终验证**: 使用 `verification-before-completion` 交付前门禁
7. **同步判断**: 判断 README、AGENTS、spec、openspec/specs 是否需要更新
8. **归档**: `openspec archive <name>`

## 当前 Capability Specs

| Capability | 路径 |
|------------|------|
| account-registration | `openspec/specs/account-registration/spec.md` |
| captcha-provider | `openspec/specs/captcha-provider/spec.md` |
| mail-provider | `openspec/specs/mail-provider/spec.md` |

## 验证命令

```bash
openspec validate --all
openspec list --json
openspec status --change "<name>" --json
```

## CodeGraph 集成

CodeGraph 已接入本项目，用于：
- 定位入口和调用链
- 分析影响面
- 发现候选测试

CodeGraph 不替代 `rg` 和源码精读，SQL、配置、权限、运行时行为必须再用 `rg` 补盲。

## 高风险检查

本项目是 Python 脚本集，高风险关注点：

| 类型 | 关注点 | 验证 |
|------|--------|------|
| 密钥/配置 | `config.json` 含 API Key、代理、邮箱密码 | 确认 `.gitignore` 已忽略 |
| 验证码 | 2captcha / anticaptcha / browser / cdp 切换 | `python -m py_compile captcha_solver.py` |
| 邮箱 provider | 临时邮箱 API 变化 | `python -m py_compile mail_provider.py` |
| 目标站点 | `site_url`、邀请码、ctoken/sessionId | 抓取响应日志确认 |
| 输出文件 | `accounts.json` / `user_info.json` 格式 | 对比示例输出 |

## 多客户端协作

本项目支持 Codex、Claude Code、Cursor、Gemini、GitHub Copilot 等多 AI 客户端协作。
通用规则见项目根 `AGENTS.md`，各客户端补充规则见各自专用文件。

OpenSpec 工件是所有客户端共享的单一事实源，任何客户端修改都必须遵守本文件定义的生命周期。
