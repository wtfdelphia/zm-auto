# 自动注册机

> ⚠️ **免责声明 / Disclaimer**
>
> 本项目仅供学习和研究用途，旨在帮助开发者理解 HTTP 协议分析、API 逆向工程、以及反爬虫机制的工作原理。
>
> - 本项目不针对任何特定网站或服务，所有目标地址均为用户自行配置
> - 使用本项目产生的任何账号、API Key 或其他后果由使用者自行承担
> - 使用者需自行确保遵守目标网站的服务条款（ToS）及当地法律法规
> - 作者不对任何因使用或滥用本项目而导致的后果负责
> - 如目标站点方认为本项目侵犯其权益，请联系移除
>
> This project is for educational and research purposes only. It is designed to help developers understand HTTP protocol analysis, API reverse engineering, and anti-bot mechanisms. Users are solely responsible for their own actions and must comply with all applicable terms of service and laws.

---

全自动账号注册 + API Key 获取。支持三种验证码方案：**2captcha 打码平台**（纯 HTTP）、**本地 Playwright 浏览器**（免费）、**CDP 人工介入**（免费，最稳）。

## 架构

```
mail_provider.py     ← 7 个临时邮箱 provider（复刻自 chatgpt2api）
captcha_solver.py    ← 验证码求解器（2captcha / anticaptcha / Playwright / CDP）
register.py          ← 注册主流程 + CLI（纯 HTTP, curl_cffi）
config.json          ← 运行时配置
accounts.json        ← 注册结果输出
```

## 验证码方案

| 方案          | provider       | 说明                                                   | 成本         |
| ------------- | -------------- | ------------------------------------------------------ | ------------ |
| 2captcha 打码 | `"2captcha"` | 纯 HTTP，不依赖浏览器                                  | ~$0.005/账号 |
| 本地浏览器    | `"browser"`  | Playwright + Chromium，本地解 Turnstile + reCAPTCHA v2 | 免费         |
| CDP 人工介入  | `"cdp"`      | 连接你的 Chrome，人工点一下验证码，最稳                | 免费         |

三种方案可以随时切换，只需改 `config.json` 里的 `captcha.provider`。

## 注册流程（~30s/个）

```
1. 创建临时邮箱（CF temp mail / GPTMail / 等 7 种）
2. GET /login → 自动获取 ctoken cookie
3. 解 Turnstile → token（2captcha ~12s / 浏览器 ~15s / CDP 人工）
4. POST /api/login/email/code/send → 发验证码
5. 邮箱轮询取 6 位验证码（~5s）
6. POST /api/login/email/code/verify → 登录
7. GET /api/user/info → 检查 needVerify
8. 解 reCAPTCHA v2 → token（2captcha ~15s / 浏览器 ~20s / CDP 人工）
9. POST /api/login/recaptcha/verification → 解锁白名单
10. POST /api/api_key/create → 拿到 sk-ai-v1-... 密钥
```

## 依赖

**2captcha 方案（纯 HTTP）**：

```bash
pip install curl_cffi requests urllib3
```

**浏览器方案（额外依赖）**：

```bash
pip install playwright playwright-stealth SpeechRecognition pydub
python -m playwright install chromium
```

## 配置

```bash
cp config.example.json config.json
# 编辑 config.json
```

### 邮箱 Provider（7 选 1+）

| type                      | 说明                            | 必填字段                                     |
| ------------------------- | ------------------------------- | -------------------------------------------- |
| `cloudflare_temp_email` | Cloudflare Workers 自建临时邮箱 | `api_base`, `admin_password`, `domain` |
| `gptmail`               | GPTMail (mail.chatgpt.org.uk)   | `api_key`                                  |
| `tempmail_lol`          | TempMail.lol API v2             | `api_key`(可选), `domain`(可选)          |
| `duckmail`              | DuckMail                        | `api_key`, `default_domain`              |
| `moemail`               | MoEmail 自建                    | `api_base`, `api_key`, `domain`        |
| `inbucket`              | Inbucket 自建                   | `api_base`, `domain`                     |
| `yyds_mail`             | YYDSMail                        | `api_base`, `api_key`, `domain`        |

### Captcha

**2captcha 方案**（打码平台）：

```json
"captcha": {
    "provider": "2captcha",
    "api_key": "你的2captcha-key"
}
```

支持 `2captcha` 和 `anticaptcha`。Turnstile + reCAPTCHA v2 都通过打码 API 解决。

**浏览器方案**（本地 Playwright）：

```json
"captcha": {
    "provider": "browser",
    "api_key": "",
    "browser": {
        "headless": true,
        "stealth": true
    }
}
```

无需 api_key，使用本地 Chromium 浏览器自动完成 Turnstile 和 reCAPTCHA v2 挑战。reCAPTCHA 遇到图片挑战时自动降级为音频挑战 + 语音识别。

**CDP 方案**（人工介入，推荐）：

```json
"captcha": {
    "provider": "cdp",
    "api_key": "",
    "browser": {
        "cdp_url": "http://127.0.0.1:9222"
    }
}
```

使用前需要先启动 Chrome 并开启远程调试端口：

```bash
open -a "Google Chrome" --args \
  --remote-debugging-port=9222 \
  --proxy-server="http://127.0.0.1:7890" \
  --user-data-dir=/tmp/chrome-cdp
```

脚本会自动连接你的 Chrome，导航到目标页面，等待你手动完成验证码后自动继续。Turnstile 和 reCAPTCHA 都支持，是最稳定的免费方案。

### 站点配置

所有脚本的目标站点地址统一从 `config.json` 的 `site_url` 读取，不再硬编码。

```json
{
  "site_url": "https://zenmux.ai",
  "invite_code": ""
}
```

- `site_url`: 目标站点根地址，脚本会自动拼接 `/api`、`/login`、`/platform` 等路径。
- `invite_code`: 邀请码。配置后：
  - CDP 登录时会先访问 `/invite/<invite_code>`，随后自动跳转到登录页；
  - 若登录页存在邀请码输入框，脚本会自动填入；
  - 纯 HTTP 流程也会先访问邀请链接，再获取 `ctoken`。

### 自动创建 API Key

`read_user_info.py` 在无 API Key 时可根据配置自动创建：

```json
{
  "api_key_name": "auto",
  "auto_create_api_key": true
}
```

优先级：`--create-key` / `--auto-create-key` 等 CLI 参数 > `auto_create_api_key` > 配置了 `api_key_name`。

## 使用

```bash
# 单个注册
python register.py -n 1

# 5 个账号，2 并发
python register.py -n 5 -t 2

# 走代理（浏览器方案也会自动透传代理）
python register.py -n 3 --proxy http://127.0.0.1:7897
```

## 输出

`accounts.json`：

```json
[
  {
    "email": "tmpabc@example.com",
    "user_id": "2625US...",
    "api_key": "sk-ai-v1-xxxx...xxxx",
    "key_name": "abc123",
    "created_at": "2026-06-18T..."
  }
]
```

## 读取已登录账号（read_user_info.py）

如果你已经通过浏览器登录了目标站点，可以用 `read_user_info.py` 直接读取当前用户信息、已有 API Key，并在没有 API Key 时自动创建一个。

```bash
# 读取用户信息和 API Keys（若未配置 API Key 会自动创建）
python read_user_info.py

# 导出为 sub2api 兼容格式
python read_user_info.py --export-sub2api

# 强制创建 API Key（即使已有也新建）
python read_user_info.py --create-key

# 手动控制是否自动创建
python read_user_info.py --auto-create-key      # 无 key 时自动创建
python read_user_info.py --no-auto-create-key   # 不自动创建
```

### 自动创建逻辑

脚本按以下优先级判断是否自动创建：

1. `--create-key` 参数：总是触发创建
2. `--auto-create-key` / `--no-auto-create-key`：强制开启/关闭
3. `config.json` 中的 `auto_create_api_key`：显式开关
4. `config.json` 中的 `api_key_name`：配置此项时默认允许自动创建

```json
{
  "api_key_name": "auto"
}
```

- `"api_key_name": "auto"`：随机生成 6 位名称
- `"api_key_name": "mykey"`：固定使用 `mykey` 作为名称

## API Key 用法

```bash
curl https://your-target-site/api/v1/chat/completions \
  -H "Authorization: Bearer sk-ai-v1-..." \
  -H "Content-Type: application/json" \
  -d '{"model":"z-ai/glm-4.6v-flash-free","messages":[{"role":"user","content":"hi"}]}'
```

> ⚠️ endpoint 是 `<site_url>/api/v1/chat/completions`，不是 `/v1/chat/completions`

## 成本

| 项目         | 2captcha 方案                    | 浏览器方案   | CDP 方案 |
| ------------ | -------------------------------- | ------------ | -------- |
| Turnstile    | ~$0.002/次                       | 免费         | 免费     |
| reCAPTCHA v2 | ~$0.003/次                       | 免费         | 免费     |
| 邮箱         | 免费（CF temp mail）             | 免费         | 免费     |
| 单账号       | **~$0.005** | **$0** | **$0** |          |
| 单账号耗时   | ~30s                             | ~35s         | 人工     |

## 注意事项

1. **ctoken** 从 `/login` 的 Set-Cookie 自动获取
2. **sessionId** 由 `/login/email/code/verify` 的 Set-Cookie 设置，curl_cffi 自动捕获
3. **API Key 脱敏**: create 返回 `token: "***"`，list 返回 `sk-ai-...末4位`。注册机从 list 取 key
4. **白名单**: 新用户必须过 reCAPTCHA 才能用 API
5. **Free Plan**: 5 Flows / 5h
6. **浏览器方案**: 首次运行会自动启动 Chromium（headless），性能取决于机器配置。确保已执行 `python -m playwright install chromium`
7. **CDP 方案**: 需要先手动启动 Chrome（见配置说明），验证码由人工完成，脚本自动检测并继续。最稳定，不会被反爬检测拦截
