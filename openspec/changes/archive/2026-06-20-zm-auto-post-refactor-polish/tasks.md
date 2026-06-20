## Tasks

### 1. Tooling 清理

- [x] 1.1 更新 `pyproject.toml`：删除 mypy exclude 中已删除的脚本；从 ruff ignore 中移除 `F401`、`F841`。
- [x] 1.2 运行 `ruff check zm_auto/ tests/`，修复暴露的 unused import / unused variable。
- [x] 1.3 运行 `mypy zm_auto/`，确认无新增类型错误。

### 2. 库代码日志化

- [x] 2.1 `zm_auto/providers/base.py`：将 DEBUG print 改为 `logger.debug`。
- [x] 2.2 `zm_auto/providers/cloudflare.py`：将 DEBUG print 改为 `logger.debug`。
- [x] 2.3 `zm_auto/services/user_info/core.py`：将非用户-facing print 改为 `logger.info`/`logger.warning`。
- [x] 2.4 `zm_auto/services/user_info/export.py`：同上。
- [x] 2.5 `zm_auto/captcha/cdp.py`：将提示用户手动验证的 print 改为 `logger.info`。
- [x] 2.6 `zm_auto/captcha/login_solver.py`：将日志/提示 print 改为 `logger.info`/`logger.warning`。
- [x] 2.7 `zm_auto/services/account_status.py`：将诊断输出改为 `logger.info`。
- [x] 2.8 `zm_auto/services/user_info/__init__.py`：将 CDP 提示输出改为 `logger.info`。
- [x] 2.9 `zm_auto/services/registrar_class.py`、`tempmail_lol.py`：将 DEBUG print 改为 `logger.debug`。
- [x] 2.10 `zm_auto/services/registrar_core.py`、`captcha/login.py`：将 print 改为 `logger.info`。
- [x] 2.11 运行 `rg "print\\(" zm_auto/`，确认仅剩 CLI handler 中的用户-facing 输出。

### 3. CDPSession 网络录制

- [x] 3.1 在 `CDPSession.__init__` 中新增录制状态字段。
- [x] 3.2 实现 `enable_recording()`、`get_recording()`、`clear_recording()`。
- [x] 3.3 在 `new_page()` 中，若录制启用，为 page 添加 `request`/`response` 事件监听器。
- [x] 3.4 新增 `tests/test_cdp_session.py`，覆盖录制功能。

### 4. Provider 配置校验

- [x] 4.1 在 `BaseMailProvider` 中新增 `validate_config(cls, config)` 类方法，默认校验 `required_fields`。
- [x] 4.2 在 `create_mailbox` 中调用 `provider_class.validate_config(entry)`。
- [x] 4.3 新增 `tests/test_provider_validation.py`，覆盖有效/无效配置。

### 5. doctor 增强

- [x] 5.1 `zm_auto/cli/commands.py`：为 `doctor` 添加 `--compact` flag。
- [x] 5.2 `zm_auto/cli/doctor.py`：实现紧凑输出格式，包含 config loaded、provider count、cdp reachable、依赖版本摘要。
- [x] 5.3 运行 `python -m zm_auto doctor --compact` 验证输出。

### 6. Agent 可发现性

- [x] 6.1 新增 `.codex/zm-auto/SKILL.md`。
- [x] 6.2 内容包含：项目描述、主要入口命令、安全约束、依赖版本要求。

### 7. 验证与收尾

- [x] 7.1 `python -m compileall zm_auto/`
- [x] 7.2 `ruff check zm_auto/ tests/`
- [x] 7.3 `mypy zm_auto/`
- [x] 7.4 `python -m pytest tests/ -v` 全绿
- [x] 7.5 `python -m zm_auto doctor --compact` 正常
- [x] 7.6 `openspec validate --all`
- [x] 7.7 `spec-compliance-check`
- [x] 7.8 `verification-before-completion`
