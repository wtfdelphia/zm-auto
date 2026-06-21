## MODIFIED Requirements

### Requirement: CDP 人工介入方案

系统 SHALL 通过 Chrome DevTools Protocol 连接远程 Chrome，由人工完成验证码，并自动处理登录后的页面跳转。

#### Scenario: 验证码后自动跳转额外验证页

- **WHEN** 邮箱验证码填写完成后
- **THEN** 页面自动跳转到 `/verify?method=unknown` 进行额外人机验证
- **AND** 系统等待至少 15 秒
- **AND** 页面最终自动跳转到 `/platform` 或站点根路径 `/`

#### Scenario: 额外验证完成后跳转根路径

- **WHEN** `/verify?method=unknown` 页面的人工验证完成后
- **THEN** 页面自动跳转到 `https://zenmux.ai/`
- **AND** 系统识别该 URL 为登录成功
- **AND** 登录流程成功完成

## ADDED Requirements

无。

## REMOVED Requirements

无。
