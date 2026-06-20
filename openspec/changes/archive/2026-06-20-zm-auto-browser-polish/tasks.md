## Tasks

### 1. HAR 导出模块

- [x] 1.1 创建 `zm_auto/cdp/har.py`，实现 `_build_har(recording)` 和 `export_har(recording, title="zm-auto")` 函数。
- [x] 1.2 实现 HAR `log.version`、`creator`、`entries` 结构。
- [x] 1.3 每个 entry 包含 `request`（method/url/headers）、`response`（status/statusText/headers/content）、`startedDateTime`、`time`、`timings`。
- [x] 1.4 在 `CDPSession` 中新增 `export_har()` 方法，调用 har 模块。
- [x] 1.5 新增 `tests/test_cdp_har.py`：验证空录制、单条录制、时间格式、JSON 往返。

### 2. Stealth 脚本注入

- [x] 2.1 创建 `zm_auto/cdp/stealth.py`，定义 `STEALTH_SCRIPT` 字符串，覆盖 `navigator.webdriver`、`plugins`、`languages`、`window.chrome`、`navigator.permissions`。
- [x] 2.2 在 `CDPSession` 中新增 `add_stealth_scripts(page)` 方法，调用 `page.add_init_script` 注入脚本。
- [x] 2.3 新增 `tests/test_cdp_stealth.py`：使用 mock page 验证注入脚本内容和幂等性；使用真实/模拟 page 验证检测点（如环境允许）。

### 3. 结构化错误与重试

- [x] 3.1 创建 `zm_auto/errors.py`，定义：
  - `class ZmAutoError(Exception)`
  - `class RetryableError(ZmAutoError)`
  - `class RetryExhaustedError(ZmAutoError)`
  - `class RetryPolicy`
  - `def with_retry(func, policy=None, *args, **kwargs)`
- [x] 3.2 `with_retry` 支持按次数、指数退避、最大延迟、可重试异常类型。
- [x] 3.3 新增 `tests/test_errors.py`：验证正常返回、重试后成功、超过最大重试、自定义 policy。

### 4. CLI JSON 输出

- [x] 4.1 在 `zm_auto/cli/doctor.py` 中实现 `--format {text,json}` 参数处理。
- [x] 4.2 当 `--format json` 时，输出包含 `ok`、`dependencies`、`mail_providers`、`captcha_providers`、`cdp_reachable` 字段的 JSON。
- [x] 4.3 更新 `zm_auto/cli/commands.py` 中 doctor 子命令的元数据。
- [x] 4.4 新增/更新 `tests/test_cli_doctor.py`：验证 JSON 输出格式和字段存在性。

### 5. 验证与收尾

- [x] 5.1 `python -m compileall zm_auto/`
- [x] 5.2 `ruff check zm_auto/ tests/`
- [x] 5.3 `mypy zm_auto/`
- [x] 5.4 `python -m pytest tests/ -v` 全绿
- [x] 5.5 `python -m zm_auto doctor --format json` 正常
- [x] 5.6 `openspec validate --all`
- [x] 5.7 `spec-compliance-check`
- [x] 5.8 `verification-before-completion`
