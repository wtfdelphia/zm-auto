# Mail Provider Capability

## Purpose

抽象临时邮箱 provider 接口，支持 7 种 provider，统一接收验证码的接口，隐藏不同 API 差异，被 `zm_auto/services/registrar.py` 调用以轮询邮箱验证码。
## Requirements
### Requirement: Cloudflare 自建临时邮箱

系统 SHALL 通过 Cloudflare Workers 自建临时邮箱服务接收验证码。

#### Scenario: 使用 Cloudflare Temp Email 接收验证码

- **WHEN** 用户配置 mail.providers[].type 为 cloudflare_temp_email 且 api_base、admin_password、domain 正确
- **THEN** 系统通过 Cloudflare Workers API 创建临时邮箱
- **AND** 轮询收件箱获取 6 位验证码
- **AND** 返回验证码给注册流程

### Requirement: GPTMail 第三方服务

系统 SHALL 通过 GPTMail 接收验证码。

#### Scenario: 使用 GPTMail 接收验证码

- **WHEN** 用户配置 mail.providers[].type 为 gptmail 且 api_key 有效
- **THEN** 系统通过 GPTMail API 创建邮箱并轮询验证码

### Requirement: TempMail.lol 第三方服务

系统 SHALL 通过 TempMail.lol API v2 接收验证码。

#### Scenario: 使用 TempMail.lol 接收验证码

- **WHEN** 用户配置 mail.providers[].type 为 tempmail_lol
- **THEN** 系统通过 TempMail.lol API 创建邮箱并轮询验证码
- **AND** 支持可选 api_key 和 domain 配置

### Requirement: 其他邮箱 Provider

系统 SHALL 支持 DuckMail、MoEmail、Inbucket、YYDSMail 等 Provider，接口统一。

#### Scenario: 切换邮箱 Provider

- **WHEN** 用户在 config.json 中切换 mail.providers 的 enable 和 type
- **THEN** 系统使用对应 Provider 的 API 创建邮箱和轮询验证码
- **AND** 域名失效时可切换到备用 Provider

### Requirement: 验证码轮询超时

系统 SHALL 在 wait_timeout 时间内未收到验证码时超时退出。

#### Scenario: 验证码超时后退出

- **WHEN** 在 wait_timeout 时间内未收到验证码
- **THEN** 系统按 wait_interval 间隔重试
- **AND** 超时后退出并报告失败

### Requirement: Provider 配置校验钩子

`BaseMailProvider` SHALL 提供 `validate_config` 类方法。

#### Scenario: 子类可覆盖校验

- 子类可覆盖 `validate_config` 实现自定义校验。

### Requirement: 必填字段校验

默认实现 SHALL 校验 `required_fields` 中的字段在 config 字典中存在且非空。

#### Scenario: 缺失必填字段报错

- `BaseMailProvider` 子类设置 `required_fields = ["api_key"]` 后，`validate_config({})` 抛出 `ValueError`。
- `validate_config({"api_key": "x"})` 通过。

### Requirement: 工厂函数调用校验

`create_mailbox` SHALL 在实例化前调用校验，缺失时 SHALL 抛出异常。

#### Scenario: 校验失败阻止实例化

- 工厂函数在 `provider_class.validate_config(entry)` 失败时抛出异常，不再继续实例化。

## Non-Goals

- 不维护长期邮箱服务。
- 不提供邮件发送能力。

## Verification

- `python -m compileall zm_auto/providers`
- `python -m py_compile zm_auto/providers/*.py`
- 单个注册 `python -m zm_auto register -n 1` 通过邮箱验证码阶段

## Residual Risk

- 临时邮箱 API 变化或域名被墙/失效。
- 验证码邮件延迟或进入垃圾邮件。
