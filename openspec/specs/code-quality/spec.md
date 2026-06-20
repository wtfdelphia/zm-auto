# code-quality Specification

## Purpose
TBD - created by archiving change refactor-zm-auto-package. Update Purpose after archive.
## Requirements
### Requirement: pytest 测试全部通过

所有现有测试 SHALL 在重构后全部通过，import 路径更新为 `zm_auto` 包内路径。

#### Scenario: 全量测试通过

- **WHEN** 执行 `python -m pytest tests/ -v`
- **THEN** 108 个测试全部 PASSED
- **AND** 无 import 错误

#### Scenario: 测试 import 路径更新

- **WHEN** 检查 `tests/test_mail_provider.py` 的 import 语句
- **THEN** 使用 `from zm_auto.providers import ...` 而非 `from mail_provider import ...`

### Requirement: ruff 代码检查通过

系统 SHALL 通过 ruff 代码检查，无错误。

#### Scenario: ruff check 无错误

- **WHEN** 执行 `ruff check zm_auto/`
- **THEN** 退出码为 0，无错误输出

### Requirement: mypy 类型检查通过

系统 SHALL 通过 mypy 类型检查，核心公共 API（config、providers、captcha、services 的公开函数和类）无类型错误，无不必要的 `Any` 类型（与第三方库交互或合理的 `Any` 使用允许）。

#### Scenario: mypy 无关键错误

- **WHEN** 执行 `mypy zm_auto/`
- **THEN** 核心公共 API（config、providers、captcha 的公开函数）无类型错误

### Requirement: 消除重复代码

CDP 连接工具和 HTTP 会话工厂 SHALL 仅存在一份实现，被所有模块共享。

#### Scenario: CDP 工具无重复

- **WHEN** 搜索 `def _cdp_connect` 在 `zm_auto/` 下的出现次数
- **THEN** 仅在 `zm_auto/cdp/helpers.py` 中定义一次

#### Scenario: HTTP 会话工厂无重复

- **WHEN** 搜索 `def _make_session` 或 `def _make_http_session` 在 `zm_auto/` 下的出现次数
- **THEN** 仅在 `zm_auto/http.py` 中定义一次

### Requirement: JSON 读写工具统一

项目 SHALL 通过 `zm_auto/utils.py` 中的统一函数进行 JSON 文件读写。

#### Scenario: JSON 追加写入统一

- **WHEN** 注册流程需要追加结果到 `accounts.json`
- **THEN** 调用 `zm_auto.utils.append_json_records()` 而非自行实现文件操作

### Requirement: 库模块无裸 print

库模块 SHALL 不使用裸 `print` 进行调试或日志输出。

#### Scenario: print 仅出现在 CLI handler

- 运行 `rg "print\\(" zm_auto/` 仅命中 CLI handler 中的用户-facing 输出。

### Requirement: mypy exclude 清理

`pyproject.toml` 的 mypy exclude SHALL 只包含当前存在的文件；已删除脚本 SHALL 不再出现在 exclude 列表。

#### Scenario: exclude 列表无已删除脚本

- `pyproject.toml` 中无 `mail_provider.py`、`captcha_solver.py` 等已删除脚本的 exclude 项。

### Requirement: ruff 严格度提升

ruff ignore 列表 SHALL 不 blanket 忽略 `F401`（unused import）和 `F841`（unused variable）。

#### Scenario: ruff 全绿且未忽略 F401/F841

- `ruff check zm_auto/ tests/` 全绿且未忽略 F401/F841。

