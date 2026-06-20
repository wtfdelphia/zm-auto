# package-structure Specification

## Purpose
TBD - created by archiving change refactor-zm-auto-package. Update Purpose after archive.
## Requirements
### Requirement: zm_auto 包结构

项目 SHALL 以 `zm_auto/` Python 包组织所有模块，按职责分层为 providers、captcha、cdp、services、cli、importers。

#### Scenario: 包可正常导入

- **WHEN** 执行 `python -c "import zm_auto"`
- **THEN** 导入成功，无 ImportError

#### Scenario: 子模块可独立导入

- **WHEN** 执行 `from zm_auto.providers import create_mailbox`
- **THEN** 导入成功

### Requirement: 模块职责单一

每个模块 SHALL 仅承担单一职责，核心文件行数不超过 400 行。

#### Scenario: mail_provider 拆分

- **WHEN** 检查 `zm_auto/providers/` 目录
- **THEN** 包含 base.py 和 7 个 provider 文件（cloudflare.py、gptmail.py、tempmail_lol.py、duckmail.py、moemail.py、inbucket.py、yyds.py）
- **AND** 每个文件行数不超过 400 行

#### Scenario: captcha_solver 拆分

- **WHEN** 检查 `zm_auto/captcha/` 目录
- **THEN** 包含 base.py 和 3 个 solver 文件（paid_api.py 合并 2captcha + anticaptcha、browser.py、cdp.py）
- **AND** 每个文件行数不超过 400 行

#### Scenario: Registrar.register() 拆分

- **WHEN** 检查 `zm_auto/services/registrar.py`
- **THEN** `register()` 方法不超过 80 行
- **AND** 包含独立的 `_get_ctoken`、`_send_code`、`_verify_code`、`_create_api_key` 等步骤方法

### Requirement: Provider 自动发现注册

每个 mail provider SHALL 继承 `BaseMailProvider` 并通过 `__init_subclass__` 自动注册，`providers/__init__.py` 通过 `BaseMailProvider.__subclasses__()` 构建注册表，新增 provider 时无需修改工厂函数。

#### Scenario: provider 类声明元数据

- **WHEN** 检查 `zm_auto/providers/cloudflare.py`
- **THEN** `CloudflareProvider` 继承 `BaseMailProvider`
- **AND** 设置类属性 `type = "cloudflare_temp_email"` 和 `required_fields = [...]`

#### Scenario: 自动注册

- **WHEN** 导入 `zm_auto.providers` 并调用 `create_mailbox("cloudflare_temp_email", ...)`
- **THEN** 工厂函数通过 `BaseMailProvider.__subclasses__()` 找到对应 provider 类并实例化
- **AND** 不需要在 `__init__.py` 中硬编码 `if type == "cloudflare_temp_email": ...`

### Requirement: CDP 会话封装

系统 SHALL 通过 `zm_auto/cdp/session.py` 中的 `CDPSession` 上下文管理类管理 CDP 连接生命周期；服务层禁止直接调用底层 `_cdp_connect` 函数。

#### Scenario: CDPSession 生命周期

- **WHEN** 使用 `with CDPSession(cdp_url) as session:`
- **THEN** 退出上下文时自动关闭 page、browser 和 playwright

### Requirement: 依赖方向自底向上

模块依赖 SHALL 遵循 Layer 0 → Layer 4 的自底向上方向，禁止反向依赖。

#### Scenario: 底层模块不依赖上层

- **WHEN** 检查 `zm_auto/config.py` 的 import 语句
- **THEN** 不导入任何 zm_auto 内部模块（仅依赖标准库和 pydantic）

#### Scenario: 服务层依赖提供者层

- **WHEN** 检查 `zm_auto/services/registrar.py` 的 import 语句
- **THEN** 导入 providers、captcha、cdp、importers 中的模块
- **AND** 不导入 cli 中的模块

### Requirement: 根目录兼容入口

项目根目录 SHALL 保留 `register.py`、`read_user_info.py`、`check_account_status.py` 作为薄兼容入口，内部委托给 `zm_auto.cli` 对应命令。

#### Scenario: 旧命令仍可用

- **WHEN** 执行 `python register.py --help`
- **THEN** 显示与 `python -m zm_auto register --help` 相同的帮助信息

