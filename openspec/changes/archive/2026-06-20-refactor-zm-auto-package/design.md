## Context

zm-auto 当前是 7 个扁平 Python 脚本（3826 行），模块间依赖关系简单：只有 `register.py` 导入其他模块，其余 6 个文件完全独立。项目已有 108 个测试覆盖核心逻辑。重构目标是建立 `zm_auto/` Python 包，按职责分层，同时引入 Pydantic 配置、click CLI、logging、ruff/mypy。

## Goals / Non-Goals

**Goals:**
- 建立 `zm_auto/` 包，按 providers/captcha/cdp/services/cli/importers 分层
- 用 Pydantic v2 统一配置加载、校验、默认值
- 消除 CDP 连接和 HTTP 会话的代码重复
- 用 logging 替换裸 print，用 click 替换 argparse
- 拆分 mail_provider.py（8 个文件）和 captcha_solver.py（4 个文件）
- 引入 ruff + mypy 进行代码质量检查
- 所有现有测试通过，不改变外部行为

**Non-Goals:**
- 不改变目标站点协议、请求参数、验证码逻辑
- 不改变 JSON 输出格式（accounts.json、user_info.json、sub2api_export.json）
- 不新增功能需求，不修改现有 capability specs
- 不引入异步框架或数据库
- 不实现验证码 fallback 链、测试进程隔离、obstacle course、Docker devcontainer、独立 provider SKILL.md 包（后续单独变更）

## Decisions

### D1: Pydantic v2 配置模型

**选择**: Pydantic v2 `BaseModel`，`model_config = ConfigDict(extra="ignore")`

**理由**: 
- 当前代码用 `config.get("mail", {}).get("prefix", "")` 深层 dict 取值，无校验、无 IDE 补全
- Pydantic 提供类型安全、默认值、加载时校验，且是 Python 生态标准
- `extra="ignore"` 保证向后兼容——用户 config.json 中多余字段不会报错

**替代方案**: dataclass + 手动校验。放弃原因：需自行实现嵌套默认值和校验逻辑，增加维护成本。

**关键设计点**:
- `wait_interval` 默认值统一为 `2`（当前 DEFAULT_CONFIG 为 `3`，`config.example.json` 为 `2`，收敛到 `2` 以匹配示例配置）
- `2captcha` 这个 JSON key 以数字开头，Python 属性名不能以数字开头。当前代码实际使用 `captcha.api_key` 扁平字段（非 `captcha.2captcha.api_key` 嵌套），因此 Pydantic 模型直接用 `api_key: str` 即可，无需 alias
- `mail.providers` 列表是 discriminated union（按 `type` 字段区分 7 种 provider），用 `Annotated[..., Discriminator("type")]` 实现
- `config.example.json` 同步更新为与 DEFAULT_CONFIG 一致的 Schema
- `site_url` 默认值统一为 `"https://example.com"`（DEFAULT_CONFIG 原为 `"https://zenmux.ai"`，避免硬编码真实站点）
- `sub2api.upstream_base_url` 默认值统一为空字符串 `""`（DEFAULT_CONFIG 原为 `"https://example.com/api/anthropic"`），空值时 `sub2api_importer` 的 fallback 逻辑自动拼接 `{site_url}/api/anthropic`
- `mail.user_agent` 字段：DEFAULT_CONFIG 中为 `USER_AGENT` 常量引用，`config.example.json` 中为字面量字符串。收敛后 DEFAULT_CONFIG 改用字面量字符串（与 `config.example.json` 一致），`USER_AGENT` 常量移至 `zm_auto/constants.py`，Pydantic 模型在 `load_config` 时从常量注入默认值
- `auto_create_api_key` 默认值为 `false`（当前仅 `config.example.json` 有此字段，DEFAULT_CONFIG 缺失，补充到 DEFAULT_CONFIG）
- `sub2api.export` 默认值：`base_url` = `""`，`notes_path` = `"/v1/chat/completions"`，`openai_responses_supported` = `true`，`openai_responses_mode` = `"force_chat_completions"`，`model_aliases` = `{}`（当前仅 `config.example.json` 有此嵌套结构，DEFAULT_CONFIG 缺失，补充到 DEFAULT_CONFIG）

### D2: 目录分层

**选择**: 按依赖关系自底向上 5 层

```
Layer 0 (零依赖):  config.py, constants.py, logging_config.py, utils.py, exceptions.py
Layer 1 (依赖 L0): http.py, cdp/helpers.py, cdp/session.py
Layer 2 (依赖 L0-1): providers/*, captcha/*（paid_api.py 合并 2captcha + anticaptcha）, importers/*, services/account_status.py
Layer 3 (依赖 L0-2): services/registrar.py, services/user_info.py
Layer 4 (依赖 L0-3): cli/*
```

**理由**: 自底向上保证每层迁移后立即可测试，不需要 stub 或 mock 未完成的上层。

### D3: CLI 方案

**选择**: click 子命令组，入口 `python -m zm_auto`

**替代方案**: 保留 argparse。放弃原因：click 天然支持子命令组，参数声明更简洁，且与 `python -m` 模式配合更好。

**命令映射**:
```
python -m zm_auto register        ← 原 python register.py
python -m zm_auto user-info       ← 原 python read_user_info.py
python -m zm_auto account-status  ← 原 python check_account_status.py
python -m zm_auto doctor          ← 新增环境诊断
```

根目录保留薄兼容入口（`register.py` 等），内部 `from zm_auto.cli.xxx import main; main()`。

### D4: 测试迁移策略

**选择**: 保持测试文件结构不变，仅更新 import 路径

**理由**: 108 个测试已覆盖核心逻辑，结构迁移是纯机械操作。import 从 `from mail_provider import ...` 变为 `from zm_auto.providers import ...`，不需要重写测试逻辑。

### D5: CDP 去重策略

**选择**: 将 `_cdp_connect`、`_cdp_new_page`、`_extract_cookies` 抽取到 `zm_auto/cdp/helpers.py`，`read_user_info.py` 和 `cdp_solver.py` 均改为 import 共享实现

**注意**: `cdp_solver.py` 的 `_cdp_new_page` 支持 `cookies` 参数而 `read_user_info.py` 的不支持。合并时需保留该参数（可选），保证向后兼容。


### D6: 文件大小控制

**选择**: 每个核心模块文件 ≤400 行；对可能超标的文件提前拆分

**理由**: `package-structure` spec 明确要求核心文件行数不超过 400 行，且单一职责。

**具体措施**:
- `zm_auto/services/registrar.py`: 将 `register()` 拆分为 `_get_ctoken`、`_send_code`、`_verify_code`、`_create_api_key` 等步骤方法后，若仍超 400 行，则把通用注册前准备逻辑（如邮箱/验证码初始化）拆入 `zm_auto/services/registrar_utils.py`。
- `zm_auto/services/user_info.py`: 原 `read_user_info.py` 843 行，迁移后按职责拆分为：
  - `zm_auto/services/user_info.py`: 主 CLI 入口与流程编排
  - `zm_auto/services/user_info/core.py`: 核心读取/导出逻辑
  - `zm_auto/services/user_info/cdp_export.py`: CDP 模式下的 cookie/页面处理
  - 每个文件 ≤400 行。
- `zm_auto/captcha/cdp.py`: 原 `cdp_solver.py` 637 行，迁移后拆分为：
  - `zm_auto/captcha/cdp.py`: 公开的 `CDPSolver` 类与 `solve()` 入口
  - `zm_auto/captcha/cdp/_actions.py`: CDP 页面操作（点击、输入、等待）
  - `zm_auto/captcha/cdp/_recorder.py`: 截图/日志记录辅助
  - 每个文件 ≤400 行。

**验证**: 实现后运行 `find zm_auto -name '*.py' | xargs wc -l | awk '$1 > 400 {print}'`，无输出。

## Risks / Trade-offs

- **[CDP 路径回归]**: CDP 连接逻辑是注册流程最脆弱的部分，细微差异可能导致整个 CDP 模式挂掉 → 迁移后必须用 CDP 模式做一次端到端冒烟测试
- **[CDP 资源泄漏]**: `CDPSession` 上下文管理类未正确关闭 playwright/browser 会导致进程残留 → 所有 CDP 调用必须通过 `with CDPSession(...)`，`__exit__` 中确保关闭 browser/playwright
- **[config.json 兼容]**: Pydantic 模型可能与现有 config.json 不完全兼容 → `extra="ignore"` + 加载后 deep merge 默认值，确保旧配置不报错
- **[测试全部重写 import]**: 108 个测试的 import 路径需要批量更新 → 机械操作，可用 sed 批量替换，但需要逐个验证
- **[mail_provider 拆分引入循环导入]**: 拆分为 8 个文件后，`__init__.py` 需要导入所有 provider 类，可能产生循环依赖 → `__init__.py` 仅暴露工厂函数，不直接导入具体类；具体类由工厂函数内部懒加载
- **[check_account_status.py 配置行为差异]**: `check_account_status.py` 的 `load_config()` 与另两个不同——它不合并 DEFAULT_CONFIG，失败时直接返回 `{}`，各 `get_*` 函数自备硬编码 fallback。统一迁移到 Pydantic `load_config()` 后，行为从“空 dict + 自备 fallback”变为“完整默认值对象”，需确认所有调用点与新的 Pydantic 默认值兼容 → task 3.16 迁移时逐个验证 `get_cdp_url()`、`get_proxy()`、`get_site_url()` 行为不变
- **[Pydantic 新依赖]**: 增加外部依赖 → Pydantic v2 是 Python 生态标准库，维护活跃，风险可控
- **[确认门控默认行为]**: 脚本化调用可能因交互确认挂起 → 提供 `--yes`/`-y` 参数，并在 CI/文档中说明
- **[错误信封迁移]**: 引入 `ZMError` 后，原有直接抛异常的地方需要改为 `raise ZMError(...)` → 迁移时逐个替换，保持 message 不变并补充 hint

## Migration Plan

### 阶段 1: 基础设施（Layer 0）
1. 创建 `zm_auto/` 包目录
2. 实现 `config.py`（Pydantic 模型 + load_config）
3. 实现 `constants.py`（从各文件抽取常量）
4. 实现 `logging_config.py`
5. 实现 `utils.py`（JSON 读写工具）
6. 实现 `exceptions.py`（`ZMError` 标准错误信封）
7. 更新 `config.example.json` 为收敛后的 Schema
8. 运行现有测试，确认 config 加载兼容

### 阶段 2: 共享层（Layer 1）
9. 实现 `http.py`（合并 _make_session + _make_http_session）
10. 实现 `cdp/helpers.py`（合并两份 CDP 工具函数）
11. 实现 `cdp/session.py`（`CDPSession` 上下文管理类）

### 阶段 3: 叶子模块（Layer 2）
12. 拆分 `mail_provider.py` → `providers/`（base + 7 provider）
13. 实现 `BaseMailProvider.__init_subclass__` 自动注册
14. 实现 `providers/__init__.py` 工厂函数，通过 `__subclasses__()` 分发
15. 拆分 `captcha_solver.py` → `captcha/`（base + 4 solver）
16. 迁移 `sub2api_importer.py` → `importers/sub2api.py`
17. 迁移 `check_account_status.py` → `services/account_status.py`

### 阶段 4: 编排层（Layer 3）
18. 迁移 `register.py` → `services/registrar.py`（更新 import + 拆分 register() 方法）
19. 迁移 `read_user_info.py` → `services/user_info.py`（改用 CDPSession 和共享 HTTP）

### 阶段 5: CLI + 兼容层 + 质量（Layer 4-5）
20. 实现 `cli/`（click 子命令组，含 `doctor`）
21. 实现 `exceptions.py` 到 CLI 的友好输出（message + hint）
22. 为付费验证码 / API Key 创建 / CDP 人工模式增加 `--yes` 确认参数
23. 创建根目录兼容入口（薄 wrapper）
24. 更新测试 import 路径
25. 配置 ruff + mypy，修复报告的问题
26. 清理旧文件中的 DEBUG print，替换为 logging
27. 全量测试通过
28. CDP 冒烟测试：使用 `captcha.provider = "cdp"` 配置完成一次完整注册流程，确认 CDP 连接、页面导航、cookie 提取均正常

### 回滚策略
- 每个阶段完成后 git commit，阶段间独立可回滚
- 根目录兼容入口保证旧命令仍可用，降低回滚成本
- 若 Pydantic 配置加载失败，回退到原始的 dict-based load_config


### D7: CLI 命令统一注册表（借鉴 bb-browser）

**选择**: 在 `zm_auto/cli/commands.py` 中定义命令元数据注册表，click 子命令从注册表动态生成。

**理由**:
- 当前 design 仅提到用 click 子命令，但仍按文件分散声明，新增子命令需要修改多个文件
- bb-browser 的 `packages/shared/src/commands.ts` 把所有命令集中定义在 `COMMANDS` 数组，CLI 解析、daemon 分发、Hub 注册都从这里读取，是“单一定义源”
- 集中注册后，`--help` 文档、参数 schema、子命令入口都从同一处生成，避免重复和遗漏

**具体设计**:
```python
@dataclass
class CommandDef:
    name: str
    group: str
    description: str
    params: list[ParamDef]
    handler: str  # "zm_auto.cli.register:main"

COMMANDS: list[CommandDef] = [
    CommandDef("register", "auth", "...", [...], "zm_auto.cli.register:main"),
    CommandDef("user-info", "user", "...", [...], "zm_auto.cli.user_info:main"),
    CommandDef("account-status", "status", "...", [...], "zm_auto.cli.account_status:main"),
    CommandDef("doctor", "diag", "...", [...], "zm_auto.cli.doctor:main"),
]
```

`zm_auto/cli/__init__.py` 读取 `COMMANDS` 并动态添加 click 子命令。新的子命令只需在 `commands.py` 加一行，并在 `zm_auto/cli/<name>.py` 实现 handler，不需要再改 `__init__.py`。

**替代方案**: 每个子命令文件独立写 `@cli.command()` 装饰器。放弃原因：元数据分散，新增子命令容易遗漏 help 或参数，难以统一生成文档。

### D8: Provider 自动发现（借鉴 bb-browser，Pythonic 化）

**选择**: 每个 provider 继承 `BaseMailProvider`，在基类 `__init_subclass__` 中自动注册；`providers/__init__.py` 通过 `BaseMailProvider.__subclasses__()` 构建 type → class 映射。

**理由**:
- `@meta` 文档块扫描需要运行时解析 docstring，容易因格式错误失效，且类型检查器/IDE 无法感知
- `__init_subclass__` 是 Python 原生机制，新增 provider 只需继承基类，无需扫描文件
- 元数据（type, required_fields）作为类属性，与类定义同处一个位置，避免文档与代码脱节

**具体设计**:
```python
# zm_auto/providers/base.py
class BaseMailProvider(ABC):
    type: ClassVar[str]
    required_fields: ClassVar[list[str]] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.type:
            _PROVIDER_REGISTRY[cls.type] = cls
```

工厂函数：
```python
# zm_auto/providers/__init__.py
from typing import Type

def create_mailbox(provider_type: str, config: dict) -> BaseMailProvider:
    registry = {cls.type: cls for cls in BaseMailProvider.__subclasses__()}
    cls = registry.get(provider_type)
    if cls is None:
        raise ZMError(f"unknown provider: {provider_type}", hint="check mail.providers[].type in config.json")
    return cls(config)
```

**替代方案**: 保留 `@meta` 扫描。放弃原因：运行时解析脆弱、新增字段需要同步维护 docstring、测试和 lint 难以覆盖。

### D9: 验证码三层防御抽象（借鉴 browser-act）

**选择**: 将四种验证码方案映射为三层防御模型，每层实现统一的 `CaptchaSolver` 接口。

| 层级 | 方案 | 能力 | 文件 |
|---|---|---|---|
| 环境层 | `paid_api`（2captcha / anticaptcha） | 纯 HTTP 调用第三方打码 API，不打开浏览器 | `zm_auto/captcha/paid_api.py` |
| 执行层 | `browser` | 本地 Playwright 自动完成 Turnstile / reCAPTCHA | `zm_auto/captcha/browser.py` |
| 人类层 | `cdp` | 连接用户 Chrome，人工介入点验证码 | `zm_auto/captcha/cdp.py` |

**理由**:
- browser-act 的“环境层 → 执行层 → 人类层”分层清晰，与 zm-auto 现有三种方案天然对应
- 分层后 `CaptchaSolver` 的抽象不再只是“按字符串分发”，而是有明确语义：越上层越自动化、越便宜；越下层越稳定、越需人工
- `config.json` 中的 `captcha.provider` 仍保持四值（`2captcha`/`anticaptcha`/`browser`/`cdp`），但内部实现按三层组织

**关键设计点**:
- `paid_api.py` 合并 2captcha 与 anticaptcha，因为它们共享 submit/poll 模式，仅 endpoint 和参数略有不同
- 保留 `anticaptcha` 作为 `paid_api` 内部子模式，对外仍是一个独立 provider 字符串
- `browser.py` 与 `cdp.py` 分别依赖 `zm_auto/cdp/helpers.py` 中的 `CDPSession` 和 Playwright，避免重复实现页面等待、截图、cookie 提取

### D10: 不引入 Obscura

**选择**: 本次重构不引入 Obscura 浏览器引擎，也不为其预留学生 Rust/Cargo 构建路径。

**理由**:
- Obscura 是 Rust 自研浏览器引擎，v0.1.8 早期版本，自研 DOM 兼容性不足，首次构建需 5 分钟 + 数 GB
- 项目目标是整理现有 Python 代码结构，不是替换浏览器后端
- 注册流程对稳定性敏感，不能承担新浏览器引擎的兼容风险

**长期雷达**: 如果未来需要高并发、低内存占用的浏览器后端，可以重新评估 Obscura 作为 Playwright/Chromium 的替代方案，届时需要单独建立变更。

### D11: CDP 会话封装

**选择**: 在 `zm_auto/cdp/session.py` 实现 `CDPSession` 上下文管理类，替代 `_cdp_connect` + `_cdp_new_page` 的函数组合。

**理由**:
- bb-browser 的 `CdpConnection` 把连接生命周期、target 发现、事件监听封装成类，避免资源泄漏
- `zm-auto` 现有两处 CDP 连接（`read_user_info.py`、`cdp_solver.py`），迁移后统一使用 `with CDPSession(...) as session:`，自动关闭 playwright/browser/page
- 未来可在 `CDPSession` 中扩展网络事件缓存、硬超时看门狗，而不影响调用方

**具体设计**:
```python
class CDPSession:
    def __init__(self, cdp_url: str, cookies: list[dict] | None = None): ...
    def __enter__(self) -> CDPSession: ...
    def __exit__(self, exc_type, exc, tb) -> None: ...
    def new_page(self) -> Page: ...
    def close(self) -> None: ...
```

### D12: 标准错误信封

**选择**: 定义 `zm_auto/exceptions.py`，包含 `ZMError(Exception)`，带 `message` 和 `hint`。CLI 捕获后打印 `Error: {message}\nHint: {hint}`。

**理由**:
- bb-browser protocol 返回 `{error: {message, hint}}`，让调用方快速定位问题
- `zm-auto` 现有失败路径直接抛异常，对 AI Agent 不够友好
- 统一异常类型便于 CLI 统一捕获、格式化、退出码管理

### D13: 敏感操作确认门控

**选择**: 对付费验证码调用、API Key 创建、CDP 人工模式，CLI 默认交互式确认；提供 `--yes`/`-y` 跳过。

**理由**:
- browser-act 对创建浏览器、导入 Profile、代理变更等敏感操作要求显式确认，防止误操作
- 2captcha/anticaptcha 调用会产生费用，API Key 创建会产生真实资源，默认确认可降低风险
- `--yes` 参数保证自动化/CI 场景可用

### D14: doctor 自描述命令

**选择**: 新增 `python -m zm_auto doctor` 子命令，输出：配置是否可加载、可用 mail provider 列表、可用 captcha provider 列表、CDP 是否可达、输出文件路径、依赖版本提示。

**理由**:
- browser-act `get-skills` 让 Agent 在执行任务前先了解环境状态
- `doctor` 命令在调试配置、 onboarding 新用户、Agent 协作时非常有用
- 实现简单，只读不修改状态，风险极低

## Open Questions

- 无。所有设计决策已在探索阶段确认。

## New Decisions (Post-Exploration Optimization)

### D15: `__main__.py` Routes Through `main()`

**选择**: `zm_auto/__main__.py` 导入并调用 `zm_auto.cli.main()`，而不是直接调用 `cli()`。

**理由**:
- `zm_auto.cli.main()` 统一捕获 `ZMError` 并输出 `message` + `hint`，直接调用 `cli()` 会绕过错误信封
- 保持一致性：根目录兼容入口（`register.py` 等）都调用 `main()`

### D16: `CommandDef.to_json_schema()` Implemented

**选择**: 将 `CommandDef.to_json_schema()` 的占位实现替换为完整的 JSON Schema 生成，并新增 `to_json_schema_str()` 和 `registry_json_schema()`。

**理由**:
- bb-browser 的 `commands.ts` 不仅是 CLI 数据源，也供 Hub/Agent 生成调用 schema
- 之前 `to_json_schema()` 返回空字符串，AI Agent 无法利用该注册表
- 生成标准 JSON Schema 后，未来可以自动生成 Agent tool 定义

### D17: `CDPSession` Supports Manual open/close

**选择**: 在 `CDPSession` 中新增 `open()` 方法和 `browser` 属性，保留上下文管理器兼容。

**理由**:
- `CDPLoginSolver` 需要在多个方法（`login()` / `logout()`）之间保持浏览器连接，无法用一个 `with` 块覆盖
- 借鉴 bb-browser `CdpConnection` 的生命周期封装思想，但保留 Pythonic 的上下文管理器用法
- `__del__` 中兜底关闭，防止异常路径下的资源泄漏

### D18: `CDPLoginSolver` Uses `CDPSession`

**选择**: 将 `zm_auto/captcha/login_solver.py` 从直接调用 `_cdp_connect`/`_cdp_new_page` 改为使用 `CDPSession`。

**理由**:
- 设计.md D11 已要求所有 CDP 调用通过 `CDPSession`，`login_solver.py` 是最后一个未迁移的使用点
- 统一资源释放路径，降低 CDP 进程残留风险
- 保持 `CDPLoginSolver` 的公共 API 不变，调用方无需修改

### D19: Per-Package README

**选择**: 新增 `zm_auto/providers/README.md`、`zm_auto/captcha/README.md`、`zm_auto/cdp/README.md`，替代为每个类单独写 README。

**理由**:
- 借鉴 bb-browser/skills 的文档组织：统一入口文档 + 必要参考链接
- 避免过度碎片化，保持与 design.md 中 provider/solver 分组一致
- 为 Agent 协作提供快速的模块级上下文

### D20: Public API Exports in `zm_auto/__init__.py`

**选择**: 在 `zm_auto/__init__.py` 显式导出 `load_config`、`ZMError`、`make_session`、`CDPSession`、`BaseMailProvider`、`create_mailbox`、`wait_for_code`、`CaptchaSolver`。

**理由**:
- 借鉴 obscura crate 的公共 API 导出习惯：顶层 `__init__.py` 告诉用户哪些是稳定接口
- 降低外部调用者深入子模块的概率，未来内部重构更自由
- `__version__` 已存在，补充公共对象导出后 `zm_auto` 包对外更友好

### D21: `user_info/__init__.py` CDPSession 迁移

**选择**: 将 `zm_auto/services/user_info/__init__.py` 从直接使用 `_cdp_connect`/`_cdp_new_page` 改为使用 `CDPSession` 上下文管理器。

**理由**:
- 设计.md D11 要求所有 CDP 调用通过 `CDPSession`，`user_info/__init__.py` 是最后一个未迁移的使用点
- 使用 `with CDPSession(cdp_url) as session:` 后，page 关闭和 playwright 停止由 `__exit__` 自动处理，避免 finally 中手动 `pw.stop()` 的遗漏风险
- `CDPSession` 的 `ZMError` 友好提示让 CDP 未连接时的报错更统一

**清理项**:
- 移除了 `user_info/__init__.py` 中重复的 `_ts()` 和 `_print_chrome_hint()` 定义
- 验证 `rg "_cdp_connect|_cdp_new_page" zm_auto/` 仅剩 `cdp/helpers.py` 和 `cdp/session.py`

**验收**:
- `python -m pytest tests/ -q` 108 passed
- `ruff check zm_auto/ tests/` 全绿
- `mypy zm_auto/` 无错误
- `python -m compileall zm_auto/` 成功
