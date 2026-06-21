## Why

上一个修复 `fix-logout-thread-error` 改用纯 HTTP 调用服务端退出登录接口，但只带 `ctoken` 查询参数，未携带 session cookies 和 CSRF token，导致服务端返回 HTTP 500。浏览器内调用同一接口时会自动带上 cookie，因此之前能成功。

## What Changes

- 修改 `zm_auto/services/registrar_class.py` 中 `Registrar.close()`：
  - 不再关闭 HTTP session，留给 `Registrar.logout()` 复用。
- 修改 `Registrar.logout()`：
  - 使用本 Registrar 的 HTTP session 发起 POST，从而带上 session cookies；
  - 若 `csrf_token` 存在，添加 `x-csrf-token` / `x-xsrf-token` 请求头；
  - 退出后再关闭 session。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `account-registration`: CDP 退出登录请求需携带 session cookies 与 CSRF token。

## Impact

- `zm_auto/services/registrar_class.py`
