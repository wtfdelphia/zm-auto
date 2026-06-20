## Why

`refactor-zm-auto-package` 已经把 7 个扁平脚本重构为 `zm_auto/` 包，108 个测试全绿，CLI 已统一为 `python -m zm_auto`。通过深度分析本地 `bb-browser`、`obscura`、`skills` 三个项目，发现仍有若干可借鉴点能进一步提升代码质量、Agent 可发现性和运行可观测性，且不会引入外部依赖或改变外部行为。

## What Changes

1. **库代码日志化**：将 `zm_auto/providers/base.py`、`cloudflare.py`、`services/user_info/core.py`、`export.py`、`captcha/cdp.py`、`login_solver.py` 中残留的裸 `print` 替换为 `logging`，仅在 CLI handler 保留用户-facing 输出。
2. **Tooling 清理**：`pyproject.toml` 中删除对已删除脚本（`mail_provider.py` 等）的 mypy exclude；收紧 ruff ignore 列表，移除 `F401`/`F841` 的 blanket ignore。
3. **CDPSession 网络录制**：借鉴 bb-browser 网络事件与 browser-act HAR，在 `CDPSession` 新增 request/response 捕获能力，便于调试验证码和登录流程。
4. **Provider 配置校验**：借鉴 bb-browser adapter 元数据校验，在 `BaseMailProvider` 增加 `validate_config` 钩子，工厂创建时统一校验必填字段。
5. **doctor 增强**：新增 `--compact` 紧凑输出，输出依赖版本、provider 可用性、CDP 可达性，更适合 Agent 消费。
6. **Agent 可发现性**：新增 `.codex/zm-auto/SKILL.md`，描述 zm-auto 能力、入口命令和安全约束，便于 Codex 等 Agent 自动发现。

## Capabilities

- `code-quality`: 进一步减少裸 `print`，提升 ruff/mypy 严格度。
- `cli-interface`: `doctor --compact` 和 `doctor --format json` 输出增强。
- `cdp-session`: `CDPSession` 支持网络请求录制。
- `mail-provider`: provider 配置自动校验。
- `agent-discoverability`: 新增 `SKILL.md`。

## Impact

- 修改文件：`zm_auto/providers/base.py`、`cloudflare.py`、`services/user_info/core.py`、`export.py`、`captcha/cdp.py`、`login_solver.py`、`cdp/session.py`、`cli/doctor.py`、`__init__.py`、`pyproject.toml`。
- 新增文件：`.codex/zm-auto/SKILL.md`。
- 测试：现有 108 个测试应保持不变；新增 provider 校验测试。
- 不破坏 CLI 入口和 JSON 输出格式。

## Out of Scope

- 新增验证码/邮箱 provider
- 异步化重写
- Docker / devcontainer
- 真实站点 obstacle course
