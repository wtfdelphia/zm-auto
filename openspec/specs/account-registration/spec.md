# Account Registration Capability

## Purpose

自动化完成目标站点的账号注册流程，包括临时邮箱验证码接收、Turnstile / reCAPTCHA v2 验证、API Key 创建与持久化。
## Requirements
### Requirement: 根目录兼容入口透传 CLI 参数

根目录的 `register.py` 薄兼容入口 SHALL 将命令行参数透传给 `python -m zm_auto register`，使得 `python register.py <args>` 与 `python -m zm_auto register <args>` 行为一致。

#### Scenario: 通过兼容入口指定注册数量

- **WHEN** 用户执行 `python register.py -n 5`
- **THEN** 系统等价于执行 `python -m zm_auto register -n 5`
- **AND** 注册 5 个账号

#### Scenario: 通过兼容入口查看帮助

- **WHEN** 用户执行 `python register.py --help`
- **THEN** 系统显示 `register` 子命令的帮助信息

### Requirement: 单个账号注册

用户 SHALL 通过 CLI 命令 `python -m zm_auto register -n 1` 完成单个账号的全自动注册流程。根目录保留 `register.py` 薄兼容入口，执行 `python register.py -n 1` 时委托给 `python -m zm_auto register -n 1`。

#### Scenario: 使用 2captcha 方案完成单个注册

- **WHEN** 用户配置 `captcha.provider` 为 `"2captcha"` 并正确填写 `api_key`
- **THEN** 系统自动完成 Turnstile 和 reCAPTCHA v2 的纯 HTTP 求解
- **AND** 注册结果写入 `accounts.json`，包含 email、email_provider、email_token、user_id、api_key、key_name、created_at

#### Scenario: 使用浏览器方案完成单个注册

- **WHEN** 用户配置 `captcha.provider` 为 `"browser"`
- **THEN** 系统通过 Playwright + Chromium 自动完成 Turnstile 和 reCAPTCHA v2 挑战
- **AND** reCAPTCHA 图片挑战时自动降级为音频挑战 + 语音识别

#### Scenario: 使用 CDP 方案完成单个注册

- **WHEN** 用户配置 `captcha.provider` 为 `"cdp"` 并正确配置 `cdp_url`
- **THEN** 系统连接远程 Chrome 后等待人工完成验证码
- **AND** 验证码通过后自动继续后续流程

#### Scenario: 注册失败时保存邮箱信息

- **WHEN** 注册过程中任意步骤失败
- **THEN** 系统仍将已获取的邮箱信息写入 `accounts.json`
- **AND** 记录中包含 `error` 字段说明失败原因

### Requirement: 并发注册

用户 SHALL 通过 `-n N -t M` 参数并发注册多个账号。

#### Scenario: 5 个账号 2 并发

- **WHEN** 用户执行 `python -m zm_auto register -n 5 -t 2`
- **THEN** 系统以 2 个并发线程注册 5 个账号
- **AND** 每个账号独立完成邮箱创建、验证码、登录、API Key 创建

### Requirement: 邀请码支持

系统 SHALL 在配置 `invite_code` 后自动处理邀请流程。

#### Scenario: 配置邀请码后注册

- **WHEN** 用户在 `config.json` 中配置 `invite_code`
- **THEN** CDP 登录时先访问 `/invite/<invite_code>` 再跳转登录页
- **AND** 纯 HTTP 流程也先访问邀请链接再获取 `ctoken`
- **AND** 若登录页存在邀请码输入框，脚本自动填入

### Requirement: 代理支持

系统 SHALL 通过 `--proxy` 参数支持 HTTP 代理，浏览器方案也自动透传代理。

#### Scenario: 使用代理注册

- **WHEN** 用户执行 `python -m zm_auto register -n 1 --proxy http://127.0.0.1:7897`
- **THEN** 所有 HTTP 请求和浏览器流量均通过指定代理

### Requirement: register 命令支持导出 sub2api 兼容文件

系统 SHALL 允许用户通过 `python -m zm_auto register --export-sub2api` 在注册成功后直接生成/追加 `sub2api_export.json`。

#### Scenario: 单账号注册后导出

- **WHEN** 用户执行 `python -m zm_auto register -n 1 --export-sub2api`
- **THEN** 系统注册 1 个账号
- **AND** 将账号信息以 sub2api 兼容格式追加到 `sub2api_export.json`
- **AND** 文件保持 `{"exported_at", "proxies", "accounts"}` 结构

#### Scenario: 多账号追加去重

- **WHEN** 用户执行 `python -m zm_auto register -n 5 --export-sub2api`
- **AND** 其中 3 个账号注册成功
- **THEN** 系统追加 3 条账号记录到 `sub2api_export.json`
- **AND** 已存在的 `api_key` 不会重复写入

#### Scenario: 不影响自动导入

- **WHEN** `config.json` 中 `sub2api.enabled=true`
- **AND** 用户执行 `python -m zm_auto register -n 1 --export-sub2api`
- **THEN** 系统仍然按原逻辑调用 Sub2API 导入
- **AND** 同时生成 `sub2api_export.json`

### Requirement: CDP 方案注册完成后退出登录

系统 SHALL 在注册流程的所有输出文件写入完成后，再调用服务端退出登录接口。系统 SHALL 使用 HTTP POST 调用 `https://zenmux.ai/api/user/logout?ctoken=<ctoken>`，而不是通过 CDP 浏览器 evaluate 调用，以避免跨线程访问 Playwright page 对象。

#### Scenario: CDP 注册成功后不触发线程错误

- **WHEN** 用户执行 `python -m zm_auto register -n 1 --export-sub2api` 且使用 CDP provider
- **AND** 注册成功，文件写入完成
- **THEN** 系统在主线程发起 HTTP POST 到 `/api/user/logout?ctoken=<ctoken>`
- **AND** 不访问 worker 线程创建的 Playwright page 对象
- **AND** 不抛出 `cannot switch to a different thread` 异常

#### Scenario: CDP 浏览器 session 在 worker 线程关闭

- **WHEN** CDP 注册流程结束（成功或失败）
- **THEN** `Registrar.close()` 在 worker 线程内关闭 Playwright 浏览器 session
- **AND** 不产生跨线程访问错误

## Non-Goals

- 不提供分布式调度或多租户能力。
- 不保存或泄露真实密钥、密码、Cookie。

## Verification

- `python -m compileall zm_auto/`
- `python -m pytest tests/ -v`
- `python -m zm_auto --help`
- `python -m zm_auto register --help`
- `python -m zm_auto doctor --help`
- `python -m zm_auto register -n 1`（需正确配置 `config.json`）

## Residual Risk

- 目标站点接口、反爬策略变化会导致流程失效。
- 临时邮箱域名可能失效。
- 验证码方案依赖第三方服务或本地浏览器环境。
