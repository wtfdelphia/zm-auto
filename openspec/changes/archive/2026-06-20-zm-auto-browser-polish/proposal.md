## Why

`refactor-zm-auto-package` 已经把脚本重构为 `zm_auto/` 包，并在后续 polish 中补齐了 CDPSession 录制、provider 校验、doctor `--compact` 等能力。通过对比本地 `bb-browser`、`obscura` 和 `browser-act/skills` 三个项目，zm-auto 在浏览器自动化链路、可观测性和健壮性方面仍有可借鉴空间：网络录制缺少标准化导出、CDP 页面缺少反检测注入、错误处理尚未体系化。本变更在这些方向上做最小化、无外部依赖的增强。

## What Changes

1. **CDP 录制导出为 HAR**：在 `CDPSession` 已有录制能力基础上，新增 `export_har()` 方法，输出符合 HAR 1.2 规范的可读 JSON。
2. **Stealth 脚本注入**：为 CDP page 提供 `add_stealth_scripts()`，注入隐藏 `navigator.webdriver`、伪装 `plugins`/`languages`、覆盖 `window.chrome` 等脚本，降低被反自动化系统检测的概率。
3. **结构化错误与重试**：新增 `zm_auto/errors.py`，定义 `ZmAutoError`、可重试错误基类、`RetryPolicy` 与 `with_retry()`，统一 provider/CDP 调用中的重试逻辑。
4. **CLI 增强**：为 `doctor` 增加 `--format json` 输出；为 CDP 相关命令增加 `--stealth` 开关。

## Capabilities

### New Capabilities

- `cdp-har-export`: 将 CDPSession 网络录制导出为 HAR 格式。
- `cdp-stealth`: 通过 CDP 注入反检测脚本。
- `error-retry`: 统一的结构化错误与重试策略。

### Modified Capabilities

- `cli-interface`: `doctor` 命令新增 `--format json` 输出格式。
- `cdp-session`: 扩展录制 API 以支持 HAR 导出；新增 stealth 脚本注入能力。

## Impact

- 新增文件：
  - `zm_auto/cdp/har.py`
  - `zm_auto/cdp/stealth.py`
  - `zm_auto/errors.py`
  - 对应 spec 文件
- 修改文件：
  - `zm_auto/cdp/session.py`（HAR 导出、stealth 注入）
  - `zm_auto/cli/doctor.py`（JSON 输出）
  - `zm_auto/cli/commands.py`（参数解析）
- 无新增外部依赖；保持现有 CLI/JSON 输出兼容。
- 测试：新增单元测试覆盖 HAR 生成与错误重试。
