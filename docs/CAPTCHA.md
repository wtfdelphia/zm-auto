# Captcha Solver 文档

`zm_auto/captcha/` 按三层防御模型组织验证码求解方案，灵感来自 browser-act 的自动化防御分层。

## 三层防御模型

| 层级 | provider | 说明 | 文件 |
|---|---|---|---|
| 环境层 | `2captcha`, `anticaptcha` | 纯 HTTP 调用第三方打码 API | `paid_api.py` |
| 执行层 | `browser` | 本地 Playwright 自动解验证码 | `browser.py` |
| 人类层 | `cdp` | 连接用户 Chrome，人工介入 | `cdp.py` |

## Provider 详情

### 2captcha / anticaptcha

- 需要 `captcha.api_key`
- 支持 Turnstile 和 reCAPTCHA v2
- 按次计费，约 $0.005/账号

### browser

- 本地启动 Chromium/Chrome
- 自动完成 Turnstile 和 reCAPTCHA v2
- reCAPTCHA 图片挑战自动降级为音频 + 语音识别
- 需要安装 Playwright Chromium

### cdp

- 连接用户已启动的 Chrome CDP
- 导航到目标页面后等待人工完成验证码
- 最稳定，但需要人工参与

## 配置示例

```json
{
  "captcha": {
    "provider": "cdp",
    "api_key": "",
    "browser": {
      "cdp_url": "http://127.0.0.1:9222"
    }
  }
}
```

启动 Chrome：

```bash
open -a "Google Chrome" --args \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-cdp
```

## 切换方式

修改 `config.json` 中的 `captcha.provider` 即可在不同方案间切换，无需改动业务代码。
