## Why

CDP 注册流程在填写邮箱验证码后会被站点重定向到 `/verify?method=unknown` 进行额外人机验证。当前 `CDPLoginSolver._wait_for_login_or_verify` 在该页面死等 60 秒直到 URL 变成 `/` 或 `/platform`，但实际站点验证通过后可能并不会触发 Playwright 可感知的 URL 跳转，导致注册被误判为失败。同时 CDP 浏览器退出登录目前发生在 `Registrar.close()` / `worker()` 的 `finally` 中，早于 `accounts.json` / `sub2api_export.json` 文件写入，不符合“退出登录是流程最后一步”的预期。

## What Changes

- 调整 `zm_auto/captcha/login_solver.py` 中 `_wait_for_login_or_verify` 的判定策略：
  - 保留等待 `/` 或 `/platform` 跳转的能力。
  - 当 URL 为 `/verify?method=unknown` 时，等待至少 15 秒后不再死循环；改为通过浏览器内调用 `/api/user/info` 判断是否已登录。
  - 若浏览器内确认已登录，即使 URL 仍在 `/verify?method=unknown`，也视为登录成功并返回，让上层 HTTP 流程继续处理 `needVerify` / 创建 API Key 等逻辑。
- 调整 `zm_auto/services/registrar.py` 的退出登录时序：
  - `Registrar.close()` 仅关闭 HTTP session 与验证码 solver，不再调用 CDP 浏览器 logout。
  - 新增 `Registrar.logout()` 方法负责调用 CDP 浏览器 logout。
  - `run()` 在 `save_results()` 与 `_export_sub2api_json()` 完成后，再统一调用所有 `Registrar` 实例的 `logout()`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `captcha-provider`: CDP 登录流程中，对 `/verify?method=unknown` 额外验证页的等待与成功判定逻辑变更。
- `account-registration`: 注册成功后文件保存与 CDP 浏览器退出登录的时序变更。

## Impact

- `zm_auto/captcha/login_solver.py`
- `zm_auto/services/registrar.py`
- `zm_auto/services/registrar_class.py`（可能需要新增 `logout` 方法）
- 不影响 2captcha / anticaptcha / 纯 HTTP 注册流程
