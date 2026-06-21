## Overview

在 CDP 登录流程中，`CDPLoginSolver._wait_for_login_or_verify` 需要把 `/api/user/info` 的 `needVerify` 字段作为登录完成的最终判据，而不是只看 `userId` 是否存在。

## Detailed Design

### 1. 轮询 `/api/user/info`

`_wait_for_login_or_verify` 在 `/verify?method=unknown` 页面等待 `verify_wait` 秒后，开始每隔约 2 秒调用一次 `/api/user/info`。

每次拿到响应后解析：

```python
body = result.get("body") or {}
data = body.get("data") or {}
user_id = data.get("userId") or data.get("accountId")
need_verify = data.get("needVerify")
```

### 2. 成功条件

- 必须返回 HTTP 200 且 `user_id` 非空。
- 必须满足 `need_verify is False`。
- 若 `need_verify` 为 `True`，视为仍在验证中，继续等待。
- 若字段缺失（兼容旧接口），按原逻辑视为成功。

### 3. 失败与超时

- 总超时时间保持 `timeout=60` 秒不变。
- 超时仍未满足成功条件时，抛出 `RuntimeError`，附带当前 URL 与最后一次 `needVerify` 值。

### 4. 日志

- 进入 `/verify` 页面时打印 `进入额外验证页`。
- 每次轮询 `/api/user/info` 后打印 `needVerify` 值。
- 成功时打印 `验证完成，needVerify=false`。

## Affected Code

- `zm_auto/captcha/login_solver.py`: `_wait_for_login_or_verify`

## Test Plan

- `python -m py_compile zm_auto/captcha/login_solver.py`
- `python -m zm_auto register -n 1 --export-sub2api`（配置 captcha.provider=cdp）
- 观察 `/verify?method=unknown` 阶段日志，确认只有在 `needVerify=false` 后才继续创建 API Key。
