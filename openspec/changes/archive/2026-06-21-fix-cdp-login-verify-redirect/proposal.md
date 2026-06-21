## Why

CDP 登录流程在填写邮箱验证码后，当前代码会尝试点击"验证"按钮。但目标站点在输入验证码后会自动跳转到 `/verify?method=unknown` 进行额外人机验证，无需点击按钮。当前实现找不到按钮直接抛异常，导致注册失败。

## What Changes

- 修改 `CDPLoginSolver.login()` 中填写验证码后的逻辑
- 不再依赖点击验证按钮，改为等待页面 URL 跳转
- 支持 `/platform/**` 直接完成 和 `/verify?method=unknown` 后继续等待再跳转两种情况
- `/verify?method=unknown` 后至少等待 15 秒，直到跳转 `/platform`

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `captcha-provider`: 修改 CDP 登录流程中验证码提交后的等待/跳转逻辑。

## Impact

- `zm_auto/captcha/login_solver.py`
- 不影响 2captcha / browser 等验证码方案
