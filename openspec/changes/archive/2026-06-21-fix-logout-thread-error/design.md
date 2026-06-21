## Context

Playwright 的 page/context/browser 对象绑定到创建它们的线程。上一个变更把 CDP logout 从 worker 线程移到主线程执行，触发了 Playwright 的线程安全检查，导致 `cannot switch to a different thread (which happens to have exited)`。

## Goals / Non-Goals

**Goals:**
- 消除退出登录时的线程错误。
- 保持“文件写入后再调用服务端退出接口”的行为。
- 在 worker 线程内正确关闭 Playwright 浏览器 session。

**Non-Goals:**
- 不改 CLI 参数。
- 不改退出登录的触发时机。

## Decisions

1. **服务端退出登录使用纯 HTTP POST 而非 CDP 浏览器 evaluate**
   - rationale：跨线程访问 Playwright page 会报错，且服务端 logout 只需要 `ctoken`。
   - alternative：在主线程重新打开浏览器再 logout。rejected：更复杂且没必要。

2. **浏览器 session 关闭仍在 worker 线程的 `Registrar.close()` 中完成**
   - rationale：`_cdp_solver.close()` 操作 Playwright 对象，必须在创建线程执行。
   - 关闭时机仍在 `worker()` 的 `finally` 中，早于文件写入，但这只是本地资源释放，不影响服务端 session。

## Risks / Trade-offs

- [Risk] `self.ctoken` 可能为空，导致 HTTP logout 未执行。
  → Mitigation：`logout()` 开头判断 `if not self.ctoken: return`。
- [Risk] 服务端 logout 可能因网络抖动失败。
  → Mitigation：try/except 捕获，仅记录日志，不阻断流程。

## Migration Plan

无需迁移。

## Open Questions

无。
