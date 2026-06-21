## Why

`fix-cdp-logout-api-call` 把 `CDPLoginSolver.logout()` 改为调用服务端退出接口后，`registrar_class.py` 中 CDP 登录成功后立即调用 `login_solver.logout()` 会销毁当前 session。这导致后续 `user_info` 和 `/api_key/create` 请求使用已失效的 session，返回 `{"success": true, "data": null}` 或 `invalid csrf token`。

## What Changes

- 移除 CDP 登录成功后的提前 `login_solver.logout()` 调用
- 仅保留 `Registrar.close()` 中的最终退出登录，确保所有 API 调用完成后再退出

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `captcha-provider`: 调整 CDP 退出登录时机。

## Impact

- `zm_auto/services/registrar_class.py`
