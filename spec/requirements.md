# Requirements

## 项目定位

zm-auto 是一个用于学习和研究的 Python 工具集，用于自动化完成目标站点的账号注册与 API Key 获取流程，帮助开发者理解 HTTP 协议分析、API 逆向工程以及反爬虫机制。

## 功能需求

1. 账号注册
   - 通过临时邮箱接收验证码完成注册。
   - 支持 Cloudflare Temp Email、GPTMail、TempMail.lol、DuckMail、MoEmail、Inbucket、YYDSMail 等 7 种邮箱 provider。
   - 支持 ctoken 与 sessionId 自动提取与透传。

2. 验证码处理
   - 支持 2captcha / anticaptcha 打码平台。
   - 支持本地 Playwright 浏览器自动完成 Turnstile 与 reCAPTCHA v2。
   - 支持 CDP（Chrome DevTools Protocol）人工介入模式。

3. API Key 获取
   - 注册成功后自动创建 API Key。
   - 已有登录态时通过 `read_user_info.py` 读取并可选自动创建。

4. 输出与导出
   - 注册结果写入 `accounts.json`。
   - 用户信息写入 `user_info.json`。
   - 支持 sub2api 兼容格式导出。

## 非目标

- 不提供图形化管理界面。
- 不提供分布式调度或多租户能力。
- 不提供对任意第三方站点的通用注册能力，目标站点行为需通过配置适配。
- 不保存或泄露真实密钥、密码、Cookie。

## 业务边界

- 所有目标站点地址均通过 `config.json` 的 `site_url` 配置，不硬编码。
- 验证码与邮箱 provider 行为抽象在 `captcha_solver.py` 与 `mail_provider.py`，不侵入注册主流程。
- CLI 参数优先级高于配置文件，配置文件提供默认值。
