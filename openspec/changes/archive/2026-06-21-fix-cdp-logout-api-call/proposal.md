## Why

CDP 登录注册成功后，当前的 `CDPLoginSolver.logout()` 只是导航到 `/logout` 页面，没有真正调用服务端退出接口。用户反馈正确的退出方式是 POST 调用 `https://zenmux.ai/api/user/logout?ctoken=<ctoken>`。

## What Changes

- 修改 `CDPLoginSolver.logout()`，从浏览器 cookies 中提取 `ctoken`
- 向 `{site_url}/api/user/logout?ctoken=<ctoken>` 发送 POST 请求
- 请求体为空
- 可选：导航到 `/logout` 页面作为 fallback

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `captcha-provider`: 修改 CDP 退出登录行为。

## Impact

- `zm_auto/captcha/login_solver.py`
