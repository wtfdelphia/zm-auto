# Captcha Solvers

借鉴 browser-act 的三层防御模型，zm-auto 将验证码求解抽象为三层：

```
环境层 (paid_api)   -> 纯 HTTP 调用第三方打码 API（2captcha / anticaptcha）
执行层 (browser)    -> 本地 Playwright 自动完成 Turnstile / reCAPTCHA
人类层 (cdp)        -> 连接用户 Chrome，人工介入完成验证码
```

## 配置

```jsonc
{
  "captcha": {
    "provider": "2captcha",  // 或 "anticaptcha", "browser", "cdp"
    "api_key": "...",
    "browser": {
      "cdp_url": "http://127.0.0.1:9222",
      "user_data_dir": "/tmp/chrome-cdp"
    }
  }
}
```

## Provider

| Provider | Layer | File | Notes |
|---|---|---|---|
| `2captcha` | paid_api | `paid_api.py` | 需要 `api_key` |
| `anticaptcha` | paid_api | `paid_api.py` | 需要 `api_key` |
| `browser` | browser | `browser.py` | 需要 Playwright |
| `cdp` | cdp / human | `cdp.py` | 需要已启动的 Chrome CDP |

## CDP Login Solver

`login_solver.py` 中的 `CDPLoginSolver` 使用 `zm_auto.cdp.session.CDPSession` 管理 Chrome 生命周期，避免连接泄漏。
