# Captcha Provider Capability — Delta Spec

## Requirement: CDP 登录在 /verify?method=unknown 页面正确判定登录成功

系统 SHALL 在 CDP 登录流程中，当页面进入 `/verify?method=unknown` 后等待至少 15 秒；若 15 秒后 URL 仍未跳转到 `/` 或 `/platform`，系统 SHALL 通过浏览器内调用 `/api/user/info` 判断是否已登录。仅当 `/api/user/info` 返回有效的 `data.userId` **且** `data.needVerify` 为 `false` 时，系统 SHALL 视为登录成功并继续后续流程。

### Scenario: /verify?method=unknown 验证完成

- **WHEN** 用户完成邮箱验证码和额外人机验证
- **AND** 浏览器当前 URL 为 `https://zenmux.ai/verify?method=unknown`
- **AND** URL 在 15 秒内未变化
- **THEN** 系统在浏览器内调用 `/api/user/info`
- **AND** 若返回 `data.userId` 且 `data.needVerify == false`，系统视为登录成功
- **AND** 系统返回 cookies 与 csrf_token，继续后续注册流程

### Scenario: /verify?method=unknown 验证尚未完成

- **WHEN** 用户在 `/verify?method=unknown` 页面尚未完成人机验证
- **AND** `/api/user/info` 返回 `data.needVerify == true`
- **THEN** 系统继续等待并轮询 `/api/user/info`
- **AND** 总超时后仍未满足成功条件时抛出登录失败异常

### Scenario: /verify?method=unknown 验证完成后正常跳转

- **WHEN** 用户完成额外人机验证
- **AND** 浏览器 URL 跳转至 `https://zenmux.ai/` 或 `https://zenmux.ai/platform`
- **THEN** 系统立即视为登录成功
- **AND** 系统返回 cookies 与 csrf_token，继续后续注册流程
