## Why

CDP 注册流程在填写邮箱验证码后会进入 `/verify?method=unknown` 进行额外人机验证。当前 `CDPLoginSolver._wait_for_login_or_verify` 只要浏览器内 `/api/user/info` 返回 `data.userId` 就把登录视为成功，但此时 `data.needVerify` 仍为 `true`，导致上层Registrar误以为验证已通过，进而调用HTTP reCAPTCHA求解器并触发`无法连接 CDP`错误。需要让CDP登录真正等待人机验证完成（`needVerify=false`）后再返回。

## What Changes

- 调整 `zm_auto/captcha/login_solver.py` 中 `_wait_for_login_or_verify` 的判定策略：
  - 进入 `/verify?method=unknown` 后，继续等待并轮询 `/api/user/info`。
  - 仅当 `/api/user/info` 返回有效的 `data.userId`/`data.accountId` **且** `data.needVerify` 为 `false`（或不存在）时，才视为登录成功。
  - `data.needVerify` 仍为 `true` 时继续等待，直到总超时。
- 同步更新 `openspec/specs/captcha-provider/spec.md` 中 `/verify?method=unknown` 的成功判定要求。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `captcha-provider`: CDP 登录流程中，对 `/verify?method=unknown` 额外验证页的成功判定从“返回 userId”改为“返回 userId 且 needVerify=false”。

## Impact

- `zm_auto/captcha/login_solver.py`
- `openspec/specs/captcha-provider/spec.md`
- 不影响 2captcha / anticaptcha / 纯 HTTP 注册流程
