## Why

`fix-cdp-login-verify-redirect` 修复后，CDP 登录在 `/verify?method=unknown` 额外验证完成后，页面实际跳转到了站点根路径 `/`，而不是 `/platform`。当前 `_wait_for_login_or_verify()` 只把 `/platform` 视为登录成功，导致等待超时。

## What Changes

- 更新 `_wait_for_login_or_verify()`，把站点根路径 `/` 也视为登录成功
- `/verify` 额外验证完成后，页面跳转到 `/` 或 `/platform` 都算登录完成

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `captcha-provider`: 调整 CDP 登录成功 URL 判断。

## Impact

- `zm_auto/captcha/login_solver.py`
