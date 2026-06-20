## Context

`refactor-zm-auto-package` 重构后，`zm_auto/cdp/session.py` 已支持 request/response 录制，`zm_auto/cli/doctor.py` 已支持 `--compact` 紧凑输出。本变更借鉴 `bb-browser` 的 trace/HAR 思路、`obscura` 的 stealth 注入与健壮性设计、`browser-act` 的 Agent-first 输出，在现有基础上扩展：

1. 将录制数据导出为标准 HAR，便于跨工具分析；
2. 在 CDP page 注入反检测脚本，降低被目标站点识别为自动化的概率；
3. 统一错误与重试抽象，减少临时失败的噪音；
4. 为 `doctor` 增加 JSON 输出，方便 Agent/CI 消费。

## Goals / Non-Goals

**Goals:**
- 提供 `CDPSession.export_har()` 生成 HAR 1.2 JSON。
- 提供 `CDPSession.add_stealth_scripts(page)` 注入反检测脚本。
- 新增 `zm_auto/errors.py`，提供 `ZmAutoError`、`RetryableError`、`RetryPolicy`、`with_retry`。
- `doctor` 支持 `--format json`。
- 新增单元测试，覆盖 HAR 生成、错误重试逻辑。

**Non-Goals:**
- 不引入新的外部依赖（如 playwright-stealth 包）。
- 不替换现有 provider 实现，仅在需要处使用新的重试工具。
- 不创建真实站点 obstacle course（因可能受网络/目标站点变化影响）。
- 不改动现有 CLI 默认行为。

## Decisions

1. **HAR 字段最小化**：只填充 HAR 1.2 中 `entries` 必须的 `request`/`response` 字段和 `startedDateTime`/`time`/`timings`，避免过度复杂。缺失字段用合理默认值。
2. **stealth 脚本内联**：将反检测脚本直接写在 `zm_auto/cdp/stealth.py` 的字符串常量中，不依赖外部文件，避免打包问题。
3. **错误重试与现有异常兼容**：`ZmAutoError` 不替代现有异常，但鼓励新代码继承它；`with_retry` 只捕获 `RetryableError` 子类，避免改变现有调用行为。
4. **JSON doctor 与 text 并行**：`--format json` 与 `--compact` 不互斥；默认保持 text 输出。

## Risks / Trade-offs

- **stealth 脚本并非万能**：不同站点检测逻辑差异大，注入脚本只能降低风险，不能保证绕过所有检测。→ 脚本保持可扩展，后续可按站点添加 patch。
- **HAR 字段简化可能导致第三方工具解析差异**：字段缺失是合法的 HAR 1.2，但部分工具可能要求更多字段。→ 在文档中说明当前支持字段集。
- **重试可能隐藏真实问题**：默认只对 `RetryableError` 重试，且最大次数有限，避免无限重试。

## Migration Plan

- 本变更新增模块并扩展 API，不破坏现有调用。
- 现有 `CDPSession` 用户无需修改代码即可继续使用。
- 建议后续逐步将 `print`/`Exception` 替换为 `ZmAutoError` 和 `with_retry`。

## Open Questions

- 是否需要为 stealth 脚本提供按站点配置的能力？（当前不实现，保留扩展点。）
- HAR 导出是否需要支持过滤域名或 URL 模式？（当前不实现，可在后续变更中补充。）
