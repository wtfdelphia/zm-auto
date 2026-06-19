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

系统 SHALL 通过 Chrome DevTools Protocol 连接远程 Chrome，由人工完成验证码。

#### Scenario: CDP 连接远程 Chrome 等待人工完成

- **WHEN** 用户配置 captcha.provider 为 cdp 且 cdp_url 正确
- **THEN** 系统通过 CDP 连接远程 Chrome
- **AND** 导航到目标页面后等待人工完成验证码
- **AND** 检测到验证码通过后自动继续后续流程

## Non-Goals

- 不实现通用验证码识别模型。
- 不替代目标站点自身的验证策略。

## Verification

- `python -m py_compile captcha_solver.py cdp_solver.py`
- `python captcha_solver.py`（需正确配置 provider）
- 切换 provider 后运行 `register.py -n 1`

## Residual Risk

- 第三方打码平台 API 变化或余额不足。
- Playwright 依赖本地 Chromium 安装和系统环境。
- CDP 模式需要预先启动 Chrome 远程调试端口。
