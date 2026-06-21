## MODIFIED Requirements

### Requirement: CDP 人工介入方案

系统 SHALL 通过 Chrome DevTools Protocol 连接远程 Chrome，由人工完成验证码。登录流程结束后，系统 SHALL 正确调用服务端退出接口完成退出登录。

#### Scenario: CDP 登录成功后退出登录

- **WHEN** CDP 登录并完成后续注册流程后
- **THEN** 系统从浏览器 cookies 中提取 `ctoken`
- **AND** 向 `/api/user/logout?ctoken=<ctoken>` 发送 POST 请求
- **AND** 请求体为空
- **AND** 退出登录成功

## ADDED Requirements

无。

## REMOVED Requirements

无。
