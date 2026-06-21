## Context

服务端 `/api/user/logout?ctoken=<ctoken>` 接口返回 500，因为请求缺少当前 session 的 cookies，服务端无法识别要退出哪个会话。CDP 浏览器内 `fetch` 使用 `credentials: "include"` 会自动带上 cookie，而 `curl_cffi.requests.post` 不带 cookie。

## Goals / Non-Goals

**Goals:**
- 让服务端退出登录接口正确识别 session 并返回成功。
- 保持文件写入后再退出登录的顺序。

**Non-Goals:**
- 不改 CLI。
- 不改退出登录触发时机。

## Decisions

1. **复用本 Registrar 的 HTTP session 发起 logout**
   - rationale：该 session 已经过 CDP 登录后的 cookie 注入，携带了服务端需要的 session cookies。
   - alternative：把 cookies 复制到新 session。rejected：更复杂且容易遗漏。

2. **延迟关闭 HTTP session 到 logout 之后**
   - rationale：logout 需要 session 中的 cookies。
   - 浏览器（`_cdp_solver`）仍在 worker 线程的 `close()` 中关闭，避免跨线程。

## Risks / Trade-offs

- [Risk] `self.session` 在 worker 线程创建，主线程使用可能存在线程安全问题。
  → Mitigation：`curl_cffi.Session` 的 cookies 在创建后只读使用，logout 是单一 POST，风险可控。
- [Risk] 仍返回 500 可能是 CSRF 校验失败。
  → Mitigation：同时添加 `x-csrf-token` / `x-xsrf-token` 请求头。

## Migration Plan

无需迁移。

## Open Questions

无。
