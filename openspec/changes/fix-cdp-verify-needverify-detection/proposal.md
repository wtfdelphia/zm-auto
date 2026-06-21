## Why

CDP 注册流程在 `/verify?method=unknown` 额外验证页等待时，当前实现把 `/api/user/info` 只要返回 `userId`/`accountId` 就视为登录成功，导致 `needVerify: true` 时提前结束等待。后续 `registrar_class.py` 看到 `needVerify=true` 又进入 reCAPTCHA v2 分支，触发 `Playwright Sync API inside the asyncio loop` 错误，注册失败。需要让 CDP 登录等待逻辑正确识别 `needVerify` 状态。

## What Changes

- 修改 `zm_auto/captcha/login_solver.py` 的 `_wait_for_login_or_verify`：
  - 在 `/verify?method=unknown` 页通过浏览器调用 `/api/user/info` 后，将 `data.needVerify == false` 作为登录成功的必要条件。
  - `needVerify == true` 时继续循环等待，不提前返回。
  - `/platform` 或 `/` 等明确成功页仍保持原有立即返回逻辑。
- 调整 `zm_auto/services/registrar_class.py` 中 CDP 登录后的 `needVerify` 处理，确保 CDP 流程已完成后不再进入 HTTP reCAPTCHA 分支。

## Capabilities

### New Capabilities

- `cdp-verify-detection`: 基于 `/api/user/info.needVerify` 状态正确判断 CDP 额外验证是否完成。

### Modified Capabilities

- `account-registration`: 更新 CDP 登录成功判定条件，要求 `needVerify` 为 false。

## Impact

- 仅影响 `zm_auto/captcha/login_solver.py` 和 `zm_auto/services/registrar_class.py`。
- 不改动临时邮箱、验证码 solver、Sub2API 导入等模块。
- 不引入新的 CLI 参数或配置项。
