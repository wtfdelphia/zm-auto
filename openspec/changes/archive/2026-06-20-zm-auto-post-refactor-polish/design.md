## Context

`refactor-zm-auto-package` 已建立 `zm_auto/` 包结构。本轮优化从 bb-browser、obscura、browser-act/skills 借鉴具体实践，保持外部行为不变。

## Goals / Non-Goals

**Goals:**
- 消除库代码中的裸 `print`。
- 清理 `pyproject.toml` 中针对已删除文件的 mypy exclude 和过度宽松的 ruff ignore。
- 增强 `CDPSession` 的网络录制能力。
- 为 mail provider 增加统一配置校验。
- 增强 `doctor` 输出。
- 新增 `SKILL.md` 供 Agent 发现。

**Non-Goals:**
- 不改变目标站点协议或请求参数。
- 不修改 CLI 子命令名称和参数。
- 不引入新的第三方依赖。

## Decisions

### D1: 日志化策略

库模块统一使用 `logging.getLogger(__name__)`。
CLI handler 仍使用 `click.echo` 输出用户-facing 信息。

### D2: CDPSession 网络录制

新增 `CDPSession.enable_recording()` / `get_recording()` / `clear_recording()`。
录制内容：request/response URL、method、status、timestamp，不记录 response body（避免敏感信息泄露）。

### D3: Provider 配置校验

`BaseMailProvider` 新增类方法：
```python
@classmethod
def validate_config(cls, config: dict) -> None: ...
```
默认实现检查 `required_fields`。子类可覆盖。
`create_mailbox` 在实例化前调用校验。

### D4: doctor 紧凑模式

`doctor --compact` 输出单行/极简格式，便于 Agent 解析。`--format json` 保持结构化。

### D5: SKILL.md 位置

放在 `.codex/zm-auto/SKILL.md`，符合 Codex 插件/技能约定。

## Risks / Trade-offs

- 日志化后原有 `print(DEBUG...)` 输出消失；如需保留，将 DEBUG 级别日志打开即可。
- ruff 收紧后可能暴露新的 unused variable/import，需要修复。

## Verification

- `ruff check zm_auto/ tests/`
- `mypy zm_auto/`
- `python -m pytest tests/ -v`
- `python -m zm_auto doctor --compact`
- `python -m compileall zm_auto/`
