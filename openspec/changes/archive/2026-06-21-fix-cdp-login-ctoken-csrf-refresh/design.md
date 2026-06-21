## Context

`Registrar` 在初始化后访问 `/login` 获取 `ctoken`，然后 CDP 登录在浏览器中完成。浏览器登录后会设置新的 `ctoken` cookie。当前代码没有刷新这个值，导致后续 API 调用使用旧的 `ctoken`，服务端返回 `invalid csrf token`。

同时，`CDPLoginSolver` 只从 meta 和 cookie 中提取 CSRF token，没有回退到 `ctoken` cookie，导致 `self.csrf_token` 为空。

## Goals / Non-Goals

**Goals:**
- CDP 登录后使用最新的 `ctoken`
- `ctoken` 同时作为 CSRF token 回退

**Non-Goals:**
- 不改动纯 HTTP 登录流程
- 不改动其他验证码方案

## Decisions

1. 在 CDP 登录注入 cookies 后，执行 `self.ctoken = self.session.cookies.get("ctoken") or self.ctoken`
2. 在 `login_solver.py` 的 CSRF 提取逻辑中增加 `ctoken` 回退

## Risks / Trade-offs

- 若目标站点未来不再使用 `ctoken` 作为 CSRF，需要重新适配
