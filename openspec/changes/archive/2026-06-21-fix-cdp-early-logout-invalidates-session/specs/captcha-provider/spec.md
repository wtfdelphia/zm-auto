## MODIFIED Requirements

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

## ADDED Requirements

无。

## REMOVED Requirements

无。
