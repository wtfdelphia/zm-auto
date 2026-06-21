## Context

当前 CDP 注册流程存在两个耦合问题：

1. `zm_auto/captcha/login_solver.py` 中的 `_wait_for_login_or_verify` 在验证码填写后等待 URL 跳转到 `/` 或 `/platform`。当页面停在 `/verify?method=unknown` 时，它会循环等待最多 60 秒。实际运行中，额外人机验证完成后站点并不总是触发可被 Playwright 感知的 URL 跳转，导致登录被误判超时，后续注册步骤完全无法执行。

2. `zm_auto/services/registrar.py` 中 `Registrar.close()` 在 `worker()` 的 `finally` 块里调用，会触发 CDP 浏览器 logout。而 `save_results()` 与 `_export_sub2api_json()` 在 `run()` 的线程池结束后才执行，因此 logout 发生在文件写入之前。

## Goals / Non-Goals

**Goals:**
- 让 CDP 登录流程在 `/verify?method=unknown` 页面时能够正确识别登录成功状态，不再因 URL 未跳转而失败。
- 将 CDP 浏览器退出登录移动到文件写入之后，作为整个注册流程的最后一步。
- 保持现有 2captcha / anticaptcha / browser 流程不变。

**Non-Goals:**
- 不修改纯 HTTP 注册流程。
- 不修改 `config.json` 结构。
- 不重新设计 sub2api 导出格式。

## Decisions

1. **在浏览器内调用 `/api/user/info` 作为登录成功兜底判断**
   -  rationale：Playwright 的 `page.url` 只能反映地址栏变化；目标站点的验证成功可能只表现为页面状态变化或 iframe 内跳转。通过浏览器发起同源 `/api/user/info` 请求，如果返回 `data.userId`，说明 session 已建立，可直接返回。
   -  alternative：继续延长等待时间到 120 秒。 rejected：无法解决根本问题，且会显著拖慢失败用例。

2. **`/verify?method=unknown` 页面最多只等待一个固定时长（15 秒），然后进入 user info 校验**
   -  rationale：用户已说明“需要等待验证完成至少 15 秒”。15 秒后若 URL 仍未跳转，则通过 API 状态判断，避免死循环。

3. **CDP 浏览器 logout 由 `Registrar.logout()` 单独负责，不在 `close()` 中执行**
   -  rationale：`close()` 语义是释放资源，应幂等；logout 是有副作用的站点操作，且需要按顺序在文件写入后执行。
   -  alternative：在 `run()` 中直接关闭所有 registrar 再统一保存。 rejected：失败用例的中间结果也可能需要写入文件，且并发场景下需要保留 registrar 实例直到保存完成。

## Risks / Trade-offs

- [Risk] 浏览器内 `/api/user/info` 调用失败（如 CSP、CORS、网络抖动）。
  → Mitigation：try/except 捕获，失败时按原有 URL 等待逻辑继续，不引入新的失败路径。
- [Risk] 将 logout 移出 `close()` 后，若 `run()` 中途异常崩溃，可能遗漏 logout。
  → Mitigation：在 `run()` 的 `try/finally` 中执行保存与 logout，确保即使保存异常也尽量执行 logout。
- [Risk] `registrar_core.py` 中仍有同名 `worker()` / `run()`，可能与 `registrar.py` 混淆。
  → Mitigation：本次变更仅修改 `registrar.py`（CLI 实际入口），`registrar_core.py` 不做改动以保持最小范围。

## Migration Plan

无需迁移。变更仅影响 CDP provider 的注册流程行为，配置无需调整。

## Open Questions

- `/api/user/info` 是否需要带 `ctoken` 查询参数？当前浏览器请求会携带 cookie，应已包含 `ctoken`。若目标站点要求 URL 参数，可在浏览器内组装完整 URL。
