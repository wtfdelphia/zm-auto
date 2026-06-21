## MODIFIED Requirements

### Requirement: CDP 方案注册完成后退出登录

系统 SHALL 在注册流程的所有输出文件写入完成后，使用携带当前 session cookies 与 CSRF token 的 HTTP POST 请求调用 `https://zenmux.ai/api/user/logout?ctoken=<ctoken>`，以完成服务端退出登录。

#### Scenario: CDP 注册成功后退出登录返回成功

- **WHEN** 用户执行 `python -m zm_auto register -n 1` 且使用 CDP provider
- **AND** 注册成功并已完成文件写入
- **THEN** 系统使用本注册流程的 HTTP session 发起 POST 到 `/api/user/logout?ctoken=<ctoken>`
- **AND** 请求携带 session cookies
- **AND** 若 `csrf_token` 存在，请求头包含 `x-csrf-token` 与 `x-xsrf-token`
- **AND** 服务端返回 2xx 成功响应

#### Scenario: CDP 注册失败后仍尝试退出登录

- **WHEN** CDP 注册失败但已获取 ctoken
- **THEN** 文件写入后系统仍调用服务端退出登录
- **AND** 请求携带 session cookies
- **AND** 若 `csrf_token` 为空，则不添加 CSRF 请求头
