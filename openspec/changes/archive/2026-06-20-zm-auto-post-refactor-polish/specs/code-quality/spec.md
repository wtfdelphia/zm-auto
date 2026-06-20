# Code Quality

## ADDED Requirements

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
