## Why

上一个变更 `fix-cdp-verify-detection-and-logout-timing` 将 CDP 浏览器退出登录延迟到文件写入后执行，但在 `Registrar.logout()` 中仍然调用 `CDPLoginSolver.logout()`，导致在主线程中访问 worker 线程创建的 Playwright page 对象，抛出 `cannot switch to a different thread (which happens to have exited)` 错误。

## What Changes

- 修改 `zm_auto/services/registrar_class.py` 中 `Registrar.logout()`：
  - 不再调用 `CDPLoginSolver.logout()`；
  - 改用 `curl_cffi.requests.post` 直接调用服务端 `/api/user/logout?ctoken=<ctoken>` 接口。
- 修改 `Registrar.close()`：
  - 在 worker 线程内关闭 `_cdp_solver`（Playwright 浏览器 session），避免跨线程问题。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `account-registration`: CDP 退出登录的实现方式变更，行为不变（仍在文件写入后调用服务端退出接口）。

## Impact

- `zm_auto/services/registrar_class.py`
- 不影响纯 HTTP / 2captcha / browser 注册流程
