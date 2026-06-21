## Why

CDP 登录流程成功后，后续 API 调用 `/api_key/create` 返回 `invalid csrf token`。

根因：
1. `self.ctoken` 只在访问 `/login` 时获取一次，CDP 登录后 ctoken cookie 已更新，但 `self.ctoken` 未刷新
2. `CDPLoginSolver` 未把 `ctoken` 作为 CSRF token 回退，导致 `self.csrf_token` 为空

## What Changes

- CDP 登录注入浏览器 cookies 后，从 `self.session.cookies` 重新读取 `ctoken`
- `CDPLoginSolver` 提取 CSRF token 时，若 meta/cookie 中无 CSRF，则回退到 `ctoken` cookie

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `captcha-provider`: 调整 CDP 登录后 ctoken/CSRF 的刷新逻辑。

## Impact

- `zm_auto/services/registrar_class.py`
- `zm_auto/captcha/login_solver.py`
