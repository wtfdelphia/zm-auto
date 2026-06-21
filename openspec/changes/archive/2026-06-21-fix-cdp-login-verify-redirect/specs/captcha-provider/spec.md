## MODIFIED Requirements

### Requirement: CDP 人工介入方案

系统 SHALL 通过 Chrome DevTools Protocol 连接远程 Chrome，由人工完成验证码，并自动处理登录后的页面跳转。

#### Scenario: CDP 连接远程 Chrome 等待人工完成

- **WHEN** 用户配置 captcha.provider 为 cdp 且 cdp_url 正确
- **THEN** 系统通过 CDP 连接远程 Chrome
- **AND** 导航到目标页面后等待人工完成验证码
- **AND** 检测到验证码通过后自动继续后续流程

#### Scenario: 验证码后自动跳转额外验证页

- **WHEN** 邮箱验证码填写完成后
- **THEN** 页面自动跳转到 `/verify?method=unknown` 进行额外人机验证
- **AND** 系统等待至少 15 秒
- **AND** 页面最终自动跳转到 `/platform`

## ADDED Requirements

无。

## REMOVED Requirements

无。
