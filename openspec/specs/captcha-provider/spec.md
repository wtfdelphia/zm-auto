# Captcha Provider Capability

## Purpose

抽象验证码求解接口，支持 2captcha、anticaptcha、browser、cdp 四种 provider，根据 config.json 的 captcha.provider 自动分发，统一处理 Turnstile 与 reCAPTCHA v2 验证。
## Requirements
### Requirement: 2captcha 打码平台支持

系统 SHALL 通过 2captcha API Key 以纯 HTTP 方式解决 Turnstile 和 reCAPTCHA v2 验证码。

#### Scenario: 使用 2captcha 解决 Turnstile

- **WHEN** 用户配置 captcha.provider 为 2captcha 且 api_key 有效
- **THEN** 系统调用 2captcha API 创建 Turnstile 任务
- **AND** 轮询获取 token 后返回给调用方
- **AND** 单次 Turnstile 求解耗时约 12 秒

#### Scenario: 使用 2captcha 解决 reCAPTCHA v2

- **WHEN** 注册流程需要 reCAPTCHA v2 验证
- **THEN** 系统调用 2captcha API 创建 reCAPTCHA v2 任务
- **AND** 轮询获取 token 后返回给调用方

### Requirement: anticaptcha 打码平台支持

系统 SHALL 通过 anticaptcha API Key 以纯 HTTP 方式解决验证码。

#### Scenario: 使用 anticaptcha 解决 Turnstile

- **WHEN** 用户配置 captcha.provider 为 anticaptcha 且 api_key 有效
- **THEN** 系统调用 anticaptcha API 完成验证码求解
- **AND** 行为与 2captcha provider 一致

### Requirement: 本地浏览器方案

系统 SHALL 通过 Playwright + Chromium 自动完成 Turnstile 和 reCAPTCHA v2 验证。

#### Scenario: 浏览器自动完成 Turnstile

- **WHEN** 用户配置 captcha.provider 为 browser
- **THEN** 系统启动无头 Chromium 浏览器
- **AND** 自动完成 Turnstile 旋转验证
- **AND** 支持 headless 和 stealth 配置

#### Scenario: 浏览器遇到 reCAPTCHA 图片挑战时降级为音频

- **WHEN** reCAPTCHA v2 弹出图片挑战
- **THEN** 系统自动切换为音频挑战模式
- **AND** 通过 SpeechRecognition + pydub 完成语音识别

### Requirement: CDP 人工介入方案

系统 SHALL 通过 Chrome DevTools Protocol 连接远程 Chrome，由人工完成验证码。CDP 登录成功后，系统 SHALL 在后续注册流程全部完成后再调用退出登录接口。

#### Scenario: CDP 登录成功后继续后续流程

- **WHEN** CDP 登录成功
- **THEN** 系统不立即退出浏览器 session
- **AND** 继续调用 `user_info` 和 `/api_key/create` 等接口

#### Scenario: 注册完成后退出登录

- **WHEN** 注册流程全部完成（成功或失败）
- **THEN** 系统调用服务端退出接口
- **AND** 清理浏览器 session

### Requirement: CDP 登录在 /verify?method=unknown 页面正确判定登录成功

系统 SHALL 在 CDP 登录流程中，当页面进入 `/verify?method=unknown` 后等待至少 15 秒；若 15 秒后 URL 仍未跳转到 `/` 或 `/platform`，系统 SHALL 通过浏览器内调用 `/api/user/info` 判断是否已登录。仅当 `/api/user/info` 返回有效的 `data.userId` **且** `data.needVerify` 为 `false` 时，系统 SHALL 视为登录成功并继续后续流程。

#### Scenario: /verify?method=unknown 验证完成

- **WHEN** 用户完成邮箱验证码和额外人机验证
- **AND** 浏览器当前 URL 为 `https://zenmux.ai/verify?method=unknown`
- **AND** URL 在 15 秒内未变化
- **THEN** 系统在浏览器内调用 `/api/user/info`
- **AND** 若返回 `data.userId` 且 `data.needVerify == false`，系统视为登录成功
- **AND** 系统返回 cookies 与 csrf_token，继续后续注册流程

#### Scenario: /verify?method=unknown 验证完成后正常跳转

- **WHEN** 用户完成额外人机验证
- **AND** 浏览器 URL 跳转至 `https://zenmux.ai/` 或 `https://zenmux.ai/platform`
- **THEN** 系统立即视为登录成功
- **AND** 系统返回 cookies 与 csrf_token，继续后续注册流程

#### Scenario: /verify?method=unknown 验证尚未完成

- **WHEN** 用户在 `/verify?method=unknown` 页面尚未完成人机验证
- **AND** `/api/user/info` 返回 `data.needVerify == true`
- **THEN** 系统继续等待并轮询 `/api/user/info`
- **AND** 总超时后仍未满足成功条件时抛出登录失败异常

#### Scenario: /verify?method=unknown 未通过验证

- **WHEN** 用户在 `/verify?method=unknown` 页面未完成人机验证
- **AND** `/api/user/info` 未返回有效 `data.userId` 或 `data.needVerify` 仍为 `true`
- **THEN** 系统继续等待直到总超时
- **AND** 总超时后抛出登录失败异常

## Non-Goals

- 不实现通用验证码识别模型。
- 不替代目标站点自身的验证策略。

## Verification

- `python -m compileall zm_auto/captcha`
- `python -m py_compile zm_auto/captcha/*.py`
- `python -m zm_auto register -n 1`（配置 captcha.provider 后运行）
- 切换 provider 后运行 `python -m zm_auto register -n 1`

## Residual Risk

- 第三方打码平台 API 变化或余额不足。
- Playwright 依赖本地 Chromium 安装和系统环境。
- CDP 模式需要预先启动 Chrome 远程调试端口。
