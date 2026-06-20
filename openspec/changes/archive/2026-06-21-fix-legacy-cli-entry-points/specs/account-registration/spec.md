## ADDED Requirements

### Requirement: 根目录兼容入口透传 CLI 参数

根目录的 `register.py` 薄兼容入口 SHALL 将命令行参数透传给 `python -m zm_auto register`，使得 `python register.py <args>` 与 `python -m zm_auto register <args>` 行为一致。

#### Scenario: 通过兼容入口指定注册数量

- **WHEN** 用户执行 `python register.py -n 5`
- **THEN** 系统等价于执行 `python -m zm_auto register -n 5`
- **AND** 注册 5 个账号

#### Scenario: 通过兼容入口查看帮助

- **WHEN** 用户执行 `python register.py --help`
- **THEN** 系统显示 `register` 子命令的帮助信息

## MODIFIED Requirements

### Requirement: 单个账号注册

用户 SHALL 通过 CLI 命令 `python -m zm_auto register -n 1` 完成单个账号的全自动注册流程。根目录保留 `register.py` 薄兼容入口，执行 `python register.py -n 1` 时委托给 `python -m zm_auto register -n 1`。

#### Scenario: 使用 2captcha 方案完成单个注册

- **WHEN** 用户配置 `captcha.provider` 为 `"2captcha"` 并正确填写 `api_key`
- **THEN** 系统自动完成 Turnstile 和 reCAPTCHA v2 的纯 HTTP 求解
- **AND** 注册结果写入 `accounts.json`，包含 email、user_id、api_key、key_name、created_at

#### Scenario: 使用浏览器方案完成单个注册

- **WHEN** 用户配置 `captcha.provider` 为 `"browser"`
- **THEN** 系统通过 Playwright + Chromium 自动完成 Turnstile 和 reCAPTCHA v2 挑战
- **AND** reCAPTCHA 图片挑战时自动降级为音频挑战 + 语音识别

#### Scenario: 使用 CDP 方案完成单个注册

- **WHEN** 用户配置 `captcha.provider` 为 `"cdp"` 并正确配置 `cdp_url`
- **THEN** 系统连接远程 Chrome 后等待人工完成验证码
- **AND** 验证码通过后自动继续后续流程

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
