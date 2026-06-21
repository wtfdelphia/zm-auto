## MODIFIED Requirements

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

## ADDED Requirements

无。

## REMOVED Requirements

无。
