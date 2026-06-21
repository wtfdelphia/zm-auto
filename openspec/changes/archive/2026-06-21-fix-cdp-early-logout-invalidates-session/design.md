## Context

`registrar_class.py` 在 CDP 登录成功后立即调用 `login_solver.logout()`，原意是清理浏览器 session 以便下一轮注册。但 `logout()` 现在会调用服务端退出接口，导致当前 session 失效。

## Goals / Non-Goals

**Goals:**
- 避免 session 在注册流程完成前失效
- 保持最终退出登录的行为

**Non-Goals:**
- 不改动 `CDPLoginSolver.logout()` 实现
- 不改动登录流程

## Decisions

- 删除 CDP 登录后的 `login_solver.logout()` 调用
- 依赖 `Registrar.close()` 中的最终退出

## Risks / Trade-offs

- 注册失败后仍会调用退出，但这与预期一致
