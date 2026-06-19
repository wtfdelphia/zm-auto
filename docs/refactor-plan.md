# zm-auto 重构计划

> 基于 codegraph 分析的代码结构数据与静态扫描结果制定。

## 1. 项目现状

### 1.1 基本信息

| 指标 | 数值 |
|------|------|
| 文件数 | 7 个 Python 模块 + 2 个 JSON 输出文件 |
| 总代码行数 | ~3,826 行 |
| 类数量 | 15 个 |
| 函数/方法数量 | 187 个 |
| codegraph 节点数 | 285 个 |
| codegraph 调用边 | 301 条 (`calls`) |
| 未解析引用 | 0 条 |
| 测试覆盖率 | 0（无 tests/ 目录） |

### 1.2 文件规模与复杂度

| 文件 | 行数 | 函数/方法数 | 类数 | 问题摘要 |
|------|------|------------|------|----------|
| `mail_provider.py` | 1,053 | 62 / 90 nodes | 8 | 过大，provider 实现堆叠，重复模式多 |
| `cdp_solver.py` | 637 | 24 / 49 nodes | 3 | CDP 相关逻辑耦合严重 |
| `read_user_info.py` | 843 | 30 / 47 nodes | 0 | 纯过程式脚本，HTTP/CDP 分支冗长 |
| `register.py` | 585 | 17 / 44 nodes | 1 | `Registrar.register()` 长达 252 行 |
| `captcha_solver.py` | 439 | 19 / 29 nodes | 1 | 三种验证码方案分支交错 |
| `sub2api_importer.py` | 142 | 7 / 14 nodes | 1 | 规模适中 |
| `check_account_status.py` | 127 | 5 / 12 nodes | 0 | 规模小 |

### 1.3 依赖关系

```
register.py
├── mail_provider.create_mailbox / wait_for_code
├── captcha_solver.CaptchaSolver
└── sub2api_importer.Sub2APIImporter

read_user_info.py
└── sub2api_importer.Sub2APIImporter

captcha_solver.py
└── cdp_solver (浏览器/CDP 方案时)

cdp_solver.py
└── (无内部模块依赖，但逻辑与 read_user_info / captcha_solver 重复)
```

## 2. 核心问题

### 2.1 模块职责过大

- `mail_provider.py` 同时承载 7 种邮箱 Provider 的实现与公共工具函数，超过 1000 行。
- `read_user_info.py` 承担用户信息读取、API Key 创建、sub2api 导出、CDP 登录等多种职责。
- `register.py` 的 `Registrar.register()` 长达 252 行，包含登录、验证码、邮箱、API Key 创建等全链路。

### 2.2 大量重复与相似代码

- CDP 相关逻辑：`read_user_info.py` 和 `cdp_solver.py` 都包含 `_cdp_connect`、`_cdp_new_page`、cookie 提取等。
- HTTP 会话构造：`register.py`、`read_user_info.py`、`check_account_status.py` 各自实现 `load_config`、`get_proxy`、`get_site_url` 等。
- 多个文件直接写入 `accounts.json` / `user_info.json`，JSON 追加/写入逻辑分散。

### 2.3 配置管理分散

- `DEFAULT_CONFIG` 仅存在于 `register.py`，其他脚本（如 `read_user_info.py`、`check_account_status.py`）重复解析 `config.json`。
- 环境变量与配置文件混合使用，缺少统一的配置对象/Schema。

### 2.4 缺乏测试

- 没有 `tests/` 目录。
- 核心注册流程、验证码处理、邮箱解析等均未单元化，难以测试。

### 2.5 调试语句残留

- `mail_provider.py` 第 157–332 行、`register.py` 第 285–296 行存在 `DEBUG` print 语句。
- 应替换为日志器（`logging`），并支持级别控制。

### 2.6 类型注解覆盖率低

- 仅少量函数有类型提示，大量 `Any` 和动态对象。
- 验证码 solver 的浏览器/CDP 对象使用 `Any` 标注，缺少抽象。

## 3. 重构目标

1. **单一职责**：将邮箱 Provider、验证码、CDP、注册流程、用户信息、配置等拆分为独立模块。
2. **消除重复**：抽取通用工具、CDP 工具、HTTP 会话工具、配置管理到共享包。
3. **可测试**：引入 `pytest`，对核心工具函数和 Provider 接口编写单元测试。
4. **可配置**：统一配置 Schema（Pydantic / dataclasses），支持校验和默认值。
5. **可观测**：用 `logging` 替代裸 `print`，保留结构化日志扩展点。
6. **类型安全**：提高类型注解覆盖率，减少 `Any`。

## 4. 重构方案

### 4.1 目录结构调整

```
zm_auto/
├── __init__.py
├── config.py              # 统一配置 Schema 与加载
├── constants.py           # 站点 key、UA、默认值等常量
├── http.py                # 通用 HTTP 会话 / curl_cffi 封装
├── logging_config.py      # logging 初始化
├── utils.py               # 通用工具（JSON 读写、路径、时间等）
├── providers/
│   ├── __init__.py
│   ├── base.py            # BaseMailProvider 抽象
│   ├── cloudflare.py
│   ├── gptmail.py
│   ├── tempmail_lol.py
│   ├── duckmail.py
│   ├── moemail.py
│   ├── inbucket.py
│   └── yyds.py
├── captcha/
│   ├── __init__.py
│   ├── base.py            # CaptchaSolver 协议/抽象
│   ├── _2captcha.py      # 2captcha 实现
│   ├── anticaptcha.py
│   ├── browser.py
│   └── cdp.py
├── cdp/
│   ├── __init__.py
│   └── helpers.py         # CDP 连接、new_page、cookie 提取
├── services/
│   ├── __init__.py
│   ├── registrar.py       # 注册主流程（拆分后的 Registrar）
│   ├── user_info.py       # read_user_info 业务逻辑
│   └── account_status.py  # check_account_status 业务逻辑
├── cli/
│   ├── __init__.py
│   ├── register.py        # 原 register.py 的 CLI
│   ├── read_user_info.py  # 原 read_user_info.py 的 CLI
│   └── check_account_status.py
└── importers/
    └── sub2api.py         # 原 sub2api_importer.py

docs/
├── refactor-plan.md       # 本文档
└── architecture.md        # 后续补充架构说明

tests/
├── conftest.py
├── providers/
├── captcha/
└── services/
```

### 4.2 具体任务与优先级

#### P0 - 基础设施

| 任务 | 说明 | 验收标准 |
|------|------|----------|
| 统一配置管理 | 创建 `config.py`，使用 Pydantic 模型定义 Schema | `config.example.json` 可被完整校验 |
| 统一日志 | 创建 `logging_config.py`，所有脚本使用 `logging` | 无裸 `print(DEBUG...)`；支持 `--verbose` |
| 通用 HTTP 封装 | 创建 `http.py`，封装 curl_cffi Session、代理、UA | `register.py` / `read_user_info.py` 复用同一 Session |

#### P1 - 核心模块拆分

| 任务 | 说明 | 验收标准 |
|------|------|----------|
| 拆分邮箱 Provider | 每个 Provider 一个文件，继承 `BaseMailProvider` | `mail_provider.py` 从 1053 行降至 <200 行入口文件；单测通过 |
| 拆分验证码 Solver | 将 2captcha / anticaptcha / browser / cdp 拆分为子模块 | `captcha_solver.py` 仅保留统一入口 |
| 抽取 CDP 公共工具 | 将 `_cdp_connect`、`_cdp_new_page`、cookie 提取集中到 `cdp/helpers.py` | `read_user_info.py` 与 `cdp_solver.py` 复用同一工具 |
| 注册流程拆分 | 将 `Registrar.register()` 拆分为 `send_code`、`verify_code`、`create_api_key` 等步骤 | `register()` 方法 <80 行，调用清晰 |

#### P2 - 消除重复

| 任务 | 说明 | 验收标准 |
|------|------|----------|
| 统一 JSON 读写 | 创建 `utils.py::append_json_records`、`load_or_create_json` | 所有 JSON 输出复用同一函数 |
| 统一站点 URL/代理/CDP 解析 | 在 `config.py` / `http.py` 中实现 | `get_site_url`、`get_proxy`、`get_cdp_url` 不再重复定义 |
| 统一 CLI 入口 | 使用 `click` 或 `argparse` 子命令整合 CLI | `python -m zm_auto register`、`python -m zm_auto read_user_info` 可用 |

#### P3 - 测试与质量

| 任务 | 说明 | 验收标准 |
|------|------|----------|
| 添加 pytest 测试 | `tests/` 覆盖 Provider、配置、工具函数 | `pytest` 绿通 |
| 引入 Ruff/Mypy | 代码格式、导入排序、基础类型检查 | `ruff check .` 和 `mypy zm_auto` 通过 |
| 类型注解覆盖 | 核心公共 API 类型化 | 减少 `Any` 使用，关键路径有类型 |

### 4.3 依赖调整

新增开发依赖（建议写入 `pyproject.toml`）：

```toml
[project]
dependencies = [
  "curl_cffi",
  "requests",
  "urllib3",
  "playwright",
  "playwright-stealth",
  "pydantic>=2",
]

[project.optional-dependencies]
dev = [
  "pytest",
  "pytest-asyncio",
  "ruff",
  "mypy",
]
```

## 5. 风险与注意事项

1. **外部 API 行为不变**：重构仅调整代码结构，不更改目标站点协议和请求参数。
2. **验证码方案兼容性**：拆分 `CaptchaSolver` 时需保持 `provider` 参数行为一致，避免破坏现有 `config.json`。
3. **CDP 路径依赖**：多个脚本依赖 Chrome DevTools 协议，重构后应保证 `cdp_url`、`cookie` 提取逻辑一致。
4. **JSON 输出格式**：`accounts.json`、`user_info.json`、`sub2api_export.json` 的字段顺序和类型不应改变。
5. **逐步迁移**：建议先 P0/P1，再 P2/P3，每步保留可运行的端到端入口。

## 6. 迁移步骤建议

1. **第 1 阶段**：建立 `zm_auto/` 包、统一配置与日志、迁移通用工具。
2. **第 2 阶段**：拆分 `mail_provider.py` 和 `captcha_solver.py`。
3. **第 3 阶段**：迁移 `register.py`、`read_user_info.py`、`check_account_status.py` 到 `services/` 和 `cli/`。
4. **第 4 阶段**：添加测试、Ruff、Mypy，清理残留调试代码。
5. **第 5 阶段**：更新 README 和 `config.example.json` 说明，归档旧脚本或保留兼容入口。

## 7. 成功指标

- [ ] 主包 `zm_auto/` 可正常安装导入。
- [ ] `pytest` 全部通过。
- [ ] `ruff check .` 无错误。
- [ ] `mypy zm_auto` 无关键类型错误。
- [ ] 旧 CLI `python register.py` 仍可通过兼容入口运行（或已迁移到新 CLI）。
- [ ] 无裸 `print(DEBUG...)` 调试语句。
- [ ] 核心文件行数均 <400 行。

---

*本计划基于 `.codegraph/codegraph.db` 的静态分析数据与文件扫描生成。*
