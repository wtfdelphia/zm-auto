## 1. 基础设施 (Layer 0)

- [x] 1.1 创建 `zm_auto/` 包目录和 `__init__.py`
- [x] 1.2 实现 `zm_auto/config.py` — Pydantic v2 Config 模型（Config、MailConfig、CaptchaConfig、Sub2APIConfig 及 7 个 MailProviderConfig discriminated union），包含 `load_config()` 函数；在 Sub2APIConfig 中补充 `sub2api.export.*` 默认值（`base_url`、`notes_path`、`openai_responses_supported`、`openai_responses_mode`、`model_aliases`），并使其与 `config.example.json` 一致
- [x] 1.3 实现 `zm_auto/constants.py` — 从 register.py、captcha_solver.py、read_user_info.py 抽取 SITE_KEY、USER_AGENT、CDP_URL、TARGET_BASE 等常量
- [x] 1.4 实现 `zm_auto/logging_config.py` — `setup_logging(verbose: bool)` 函数
- [x] 1.5 实现 `zm_auto/utils.py` — `append_json_records()`、`load_or_create_json()` 等 JSON 工具函数（合并自 read_user_info.py 和 register.py）
- [x] 1.6 实现 `zm_auto/exceptions.py` — 标准错误信封 `ZMError(message, hint)`，CLI 统一捕获输出
- [x] 1.7 更新 `config.example.json` 为收敛后的 Schema，与 DEFAULT_CONFIG 一致
- [x] 1.8 验证：确认 `config.example.json` 与 `DEFAULT_CONFIG` 的字段结构一致，无多余/缺失字段
- [x] 1.9 创建 `zm_auto/cli/commands.py` — 命令统一注册表 `COMMANDS`，包含 `register` / `user-info` / `account-status` / `doctor` 四个子命令的元数据
- [x] 1.10 验证：确认 `COMMANDS` 字段完整，help 文本从注册表生成


## 2. 共享层 (Layer 1)

- [x] 2.1 实现 `zm_auto/http.py` — 合并 `register.py::_make_session` 和 `read_user_info.py::_make_http_session`，提供 `make_session(proxy, headers)` 工厂函数
- [x] 2.2 实现 `zm_auto/cdp/helpers.py` — 合并 `read_user_info.py` 和 `cdp_solver.py` 中的 `_cdp_connect`、`_cdp_new_page`、`_extract_cookies`，保留 `cookies` 可选参数
- [x] 2.3 实现 `zm_auto/cdp/session.py` — `CDPSession` 上下文管理类，支持 `with CDPSession(cdp_url, cookies) as session:`，`__exit__` 中确保关闭 browser/playwright
- [x] 2.4 验证：`python -m py_compile zm_auto/http.py zm_auto/cdp/helpers.py zm_auto/cdp/session.py` 通过


## 3. 叶子模块搬迁 (Layer 2)

### 3.1 mail provider 拆分与自动注册

- [x] 3.1 拆分 `mail_provider.py` → `zm_auto/providers/base.py`（`BaseMailProvider` 抽象类 + `__init_subclass__` 自动注册 + 公共工具函数）
- [x] 3.2 拆分 → `zm_auto/providers/cloudflare.py`（继承 `BaseMailProvider`，设置 `type` / `required_fields` 类属性）
- [x] 3.3 拆分 → `zm_auto/providers/gptmail.py`
- [x] 3.4 拆分 → `zm_auto/providers/tempmail_lol.py`
- [x] 3.5 拆分 → `zm_auto/providers/duckmail.py`
- [x] 3.6 拆分 → `zm_auto/providers/moemail.py`
- [x] 3.7 拆分 → `zm_auto/providers/inbucket.py`
- [x] 3.8 拆分 → `zm_auto/providers/yyds.py`
- [x] 3.9 实现 `zm_auto/providers/__init__.py` — `create_mailbox()`、`wait_for_code()` 工厂函数，通过 `BaseMailProvider.__subclasses__()` 构建注册表并分发
- [x] 3.10 验证：导入 `zm_auto.providers` 时所有 provider 类自动注册，`create_mailbox("cloudflare_temp_email", ...)` 能正确实例化

### 3.2 captcha solver 拆分

- [x] 3.11 拆分 `captcha_solver.py` → `zm_auto/captcha/base.py`（`CaptchaSolver` 协议/抽象）
- [x] 3.12 拆分 → `zm_auto/captcha/paid_api.py`（合并 2captcha + anticaptcha，共享 submit/poll 模式）
- [x] 3.13 拆分 → `zm_auto/captcha/browser.py`
- [x] 3.14 拆分 → `zm_auto/captcha/cdp.py`（改用 `zm_auto.cdp.session.CDPSession`）
- [x] 3.15 实现 `zm_auto/captcha/__init__.py` — `CaptchaSolver` 统一入口
- [x] 3.16 按三层防御模型组织 captcha 包：在 docstring 和 README 中说明 `paid_api` = 环境层，`browser` = 执行层，`cdp` = 人类层；确认 `paid_api.py` 内部同时支持 2captcha 与 anticaptcha 两种模式

### 3.3 其他叶子模块

- [x] 3.17 迁移 `sub2api_importer.py` → `zm_auto/importers/__init__.py` + `zm_auto/importers/sub2api.py`
- [x] 3.18 迁移 `check_account_status.py` → `zm_auto/services/account_status.py`（改用共享 config 和 http，验证 `get_cdp_url()`、`get_proxy()`、`get_site_url()` 迁移后行为不变）
- [x] 3.19 验证：运行 `python -m compileall zm_auto/providers zm_auto/captcha zm_auto/importers zm_auto/services` 通过，确认所有叶子模块语法正确
- [x] 3.20 验证：显式触发所有 7 个 provider 类型和 3 个 captcha solver 类型的懒加载路径（分别以每种 type 调用工厂函数），确认每个子模块文件均可被正确导入，无语法错误或 ImportError


## 4. 编排层 (Layer 3)

- [x] 4.1 迁移 `register.py` → `zm_auto/services/registrar.py`，更新 import 为 zm_auto 包内路径，拆分为 `_get_ctoken`、`_send_code`、`_verify_code`、`_create_api_key` 步骤方法，`register()` ≤ 80 行
- [x] 4.2 迁移 `read_user_info.py` → `zm_auto/services/user_info.py`，改用 `CDPSession` 和共享 http 工厂，更新 import
- [x] 4.3 验证：`python -m py_compile zm_auto/services/registrar.py zm_auto/services/user_info.py` 通过


## 5. CLI、兼容层、质量 (Layer 4-5)

### 5.1 CLI 实现

- [x] 5.1 实现 `zm_auto/cli/__init__.py` — click 主命令组，`--verbose` 全局参数
- [x] 5.2 实现 `zm_auto/__main__.py` — 模块入口，导入并调用 `zm_auto.cli` 的主命令组，使 `python -m zm_auto <subcommand>` 可用
- [x] 5.3 实现 `zm_auto/cli/register.py` — register 子命令（`-n`、`-t`、`--proxy`、`--yes`）
- [x] 5.4 实现 `zm_auto/cli/user_info.py` — user-info 子命令（`--cdp-url`、`-o`、`--export-sub2api`、`--create-key`、`--yes`）
- [x] 5.5 实现 `zm_auto/cli/account_status.py` — account-status 子命令
- [x] 5.6 实现 `zm_auto/cli/doctor.py` — doctor 子命令，输出配置、provider 列表、CDP 可达性
- [x] 5.7 实现 `zm_auto/cli/__init__.py` 基于 `commands.py` 中 `COMMANDS` 注册表动态添加 click 子命令，确保 `--help` 和参数从注册表生成
- [x] 5.8 创建根目录兼容入口：`register.py`、`read_user_info.py`、`check_account_status.py` 改为薄 wrapper（`from zm_auto.cli.xxx import main; main()`）

### 5.2 错误处理与确认门控

- [x] 5.9 在 CLI 入口统一捕获 `ZMError`，输出 `Error: {message}\nHint: {hint}`，非零退出码
- [x] 5.10 为 register 子命令添加确认门控：当 `captcha.provider` 为 `2captcha`/`anticaptcha` 或 `captcha.provider = "cdp"` 或 `auto_create_api_key = true` 时，默认提示用户确认，可用 `--yes` 跳过
- [x] 5.11 为 user-info 子命令添加确认门控：当 `--create-key` 或 `--cdp-url` 生效时默认提示用户确认，可用 `--yes` 跳过

### 5.3 测试与质量

- [x] 5.12 更新测试文件 import 路径：`tests/test_mail_provider.py`、`tests/test_captcha_solver.py`、`tests/test_register.py`、`tests/test_sub2api_importer.py`（`from mail_provider` → `from zm_auto.providers` 等，`import register` → `import zm_auto.services.registrar` 等）
- [x] 5.13 更新 `tests/test_register.py` 中依赖 DEFAULT_CONFIG 具体值的断言：`wait_interval` 从 `3` 改为 `2`，`site_url` 从 `"https://zenmux.ai"` 改为 `"https://example.com"`，`sub2api.upstream_base_url` 从 `"https://example.com/api/anthropic"` 改为 `""`
- [x] 5.14 用 `logging` 替换 `zm_auto/` 下所有模块中的 `print(DEBUG...)` 调试语句，并通过 `rg 'print\(DEBUG' zm_auto/` 全量扫描确认无残留
- [x] 5.15 配置 `pyproject.toml`：添加 `pydantic>=2`、`click` 依赖，`ruff`、`mypy` 开发依赖，ruff 和 mypy 配置
- [x] 5.16 运行 `ruff check zm_auto/` 并修复所有错误
- [x] 5.17 运行 `mypy zm_auto/` 并修复核心公共 API 的类型错误
- [x] 5.18 全量验证：`python -m pytest tests/ -v` 所有测试全部通过

### 5.4 冒烟与文档

- [x] 5.19 冒烟验证：`python -m zm_auto --help`、`python -m zm_auto register --help`、`python -m zm_auto doctor --help` 输出正常
- [x] 5.20 CDP 冒烟验证：使用 `captcha.provider = "cdp"` 配置完成一次完整注册流程，确认 CDP 连接、页面导航、cookie 提取均正常
- [x] 5.21 更新 `README.md`：入口命令、项目结构、新增依赖、CLI 用法、doctor 命令说明；将 `config.example.json` 中移除的 CDP Chrome 启动命令迁移至 README.md 或独立文档
- [x] 5.22 为每个 mail provider 创建 `README.md`（或统一 `PROVIDERS.md`），说明 provider type、必填字段、前置条件、失败策略
- [x] 5.23 为每个 captcha solver 创建 `README.md`（或统一 `CAPTCHA.md`），说明所属防御层级、provider 字符串、依赖、前置条件
- [x] 5.24 更新 `AGENTS.md` 中“常用命令”和验证策略，反映 `python -m zm_auto` 入口和新的模块路径

### 5.5 OpenSpec 收尾

- [x] 5.25 运行 spec compliance check（`spec-compliance-check` skill），确认所有 spec 要求已满足
- [x] 5.26 运行 verification-before-completion（`verification-before-completion` skill），最终交付前验证
- [x] 5.27 运行 `openspec-sync-specs`（`openspec-sync-specs` skill），将 delta specs 同步到 `openspec/specs/`，并更新 `README.md`/`AGENTS.md` 中受影响的入口说明
- [x] 5.28 更新已有 capability specs：修改 `openspec/specs/account-registration/spec.md`、`openspec/specs/mail-provider/spec.md`、`openspec/specs/captcha-provider/spec.md` 的 CLI 入口、文件路径、verification 命令，使其与 `python -m zm_auto <subcommand>` 及包内模块路径一致
- [x] 5.29 更新 `openspec/project.md` 的 Verification Baseline，将 `python -m py_compile register.py ...` 等旧命令替换为包结构下的验证命令（如 `python -m compileall zm_auto/`、`python -m zm_auto --help`）
- [x] 5.30 创建变更验证证据目录 `openspec/changes/refactor-zm-auto-package/evidence/`，存放 `pytest`、`ruff`、`mypy`、CLI `--help`、CDP 冒烟测试等输出截图或日志，供归档前审查

## 6. 借鉴优化（本轮补充）

### 6.1 CLI / 入口优化

- [x] 6.1.1 修复 `zm_auto/__main__.py` 调用 `main()`，使 `python -m zm_auto` 统一走 CLI 错误捕获路径
- [x] 6.1.2 修复 `zm_auto/cli/commands.py` 中 `CommandDef.to_json_schema()` 返回空字符串的占位实现，并新增 `to_json_schema_str()` 和 `registry_json_schema()`，为 AI Agent 调用签名提供 schema

### 6.2 CDP 一致性优化

- [x] 6.2.1 增强 `zm_auto/cdp/session.py`：`CDPSession` 新增 `open()` / `browser` 属性 / `__del__` 兜底清理，支持上下文管理器和手动 open/close 两种用法
- [x] 6.2.2 将 `zm_auto/captcha/login_solver.py` 从直接使用 `_cdp_connect`/`_cdp_new_page` 迁移为使用 `CDPSession`，统一资源生命周期管理

### 6.3 公共 API 与文档

- [x] 6.3.1 在 `zm_auto/__init__.py` 显式导出公共 API（`load_config`, `ZMError`, `make_session`, `CDPSession`, `BaseMailProvider`, `create_mailbox`, `wait_for_code`, `CaptchaSolver`）
- [x] 6.3.2 新增 `zm_auto/providers/README.md`（借鉴 bb-browser adapter 注册思想）
- [x] 6.3.3 新增 `zm_auto/captcha/README.md`（借鉴 browser-act 三层防御模型）
- [x] 6.3.4 新增 `zm_auto/cdp/README.md`（说明 CDPSession 用法与 Chrome 启动命令）

### 6.4 验证

- [x] 6.4.1 `python -m py_compile` 通过所有修改文件
- [x] 6.4.2 `ruff check zm_auto/ tests/` 全绿
- [x] 6.4.3 `python -m pytest tests/ -v` 108 passed
- [x] 6.4.4 `python -m zm_auto --help` 正常输出

### 6.5 CDP 一致性收尾

- [x] 6.5.1 迁移 `zm_auto/services/user_info/__init__.py` 使用 `CDPSession`，移除直接使用 `_cdp_connect`/`_cdp_new_page`
- [x] 6.5.2 清理 `user_info/__init__.py` 中重复的 `_ts()` / `_print_chrome_hint()` 定义
- [x] 6.5.3 验证 `rg "_cdp_connect|_cdp_new_page" zm_auto/` 仅剩 `cdp/helpers.py` 和 `cdp/session.py`
