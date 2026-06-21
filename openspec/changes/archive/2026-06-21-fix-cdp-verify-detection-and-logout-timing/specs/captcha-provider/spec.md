## MODIFIED Requirements

### Requirement: CDP 登录在 /verify?method=unknown 页面正确判定登录成功

系统 SHALL 在 CDP 登录流程中，当页面进入 `/verify?method=unknown` 后等待至少 15 秒；若 15 秒后 URL 仍未跳转到 `/` 或 `/platform`，系统 SHALL 通过浏览器内调用 `/api/user/info` 判断是否已登录。若 `/api/user/info` 返回有效的 `data.userId`，系统 SHALL 视为登录成功并继续后续流程。

#### Scenario: /verify?method=unknown 验证完成后 URL 未跳转

- **WHEN** 用户完成邮箱验证码和额外人机验证
- **AND** 浏览器当前 URL 为 `https://zenmux.ai/verify?method=unknown`
- **AND** URL 在 15 秒内未变化
- **THEN** 系统在浏览器内调用 `/api/user/info`
- **AND** 若返回 `data.userId`，系统视为登录成功
- **AND** 系统返回 cookies 与 csrf_token，继续后续注册流程

#### Scenario: /verify?method=unknown 验证完成后正常跳转

- **WHEN** 用户完成额外人机验证
- **AND** 浏览器 URL 跳转至 `https://zenmux.ai/` 或 `https://zenmux.ai/platform`
- **THEN** 系统立即视为登录成功
- **AND** 系统返回 cookies 与 csrf_token，继续后续注册流程

#### Scenario: /verify?method=unknown 未通过验证

- **WHEN** 用户在 `/verify?method=unknown` 页面未完成人机验证
- **AND** 15 秒后 `/api/user/info` 未返回有效 `data.userId`
- **THEN** 系统继续等待直到总超时
- **AND** 总超时后抛出登录失败异常
