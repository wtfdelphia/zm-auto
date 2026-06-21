## MODIFIED Requirements

### Requirement: CDP 人工介入方案

系统 SHALL 通过 Chrome DevTools Protocol 连接远程 Chrome，由人工完成验证码，并自动处理登录后的页面跳转。登录完成后，系统 SHALL 使用最新的 `ctoken` 和有效的 CSRF token 进行后续 API 调用。

#### Scenario: CDP 登录后刷新 ctoken

- **WHEN** CDP 登录成功并注入浏览器 cookies 后
- **THEN** 系统从当前 session cookies 中重新读取 `ctoken`
- **AND** 后续 API 调用使用最新的 `ctoken`

#### Scenario: CDP 登录后获取 CSRF token

- **WHEN** CDP 登录成功但页面 meta/cookie 中无 CSRF token 时
- **THEN** 系统使用 `ctoken` cookie 作为 CSRF token
- **AND** 后续 API 调用附带有效的 CSRF 请求头

## ADDED Requirements

无。

## REMOVED Requirements

无。
