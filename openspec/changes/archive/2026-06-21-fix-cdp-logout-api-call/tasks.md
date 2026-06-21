## 1. 修改 CDP 退出登录

- [x] 1.1 在 `zm_auto/captcha/login_solver.py` 的 `logout()` 中从 cookies 提取 `ctoken`
- [x] 1.2 发送 POST 请求到 `/api/user/logout?ctoken=<ctoken>`
- [x] 1.3 保留页面导航作为 fallback

## 2. 验证

- [x] 2.1 `python -m compileall zm_auto/`
- [ ] 2.2 CDP 注册测试，确认退出时调用正确的 logout 接口

## 3. OpenSpec

- [ ] 3.1 `openspec validate --changes fix-cdp-logout-api-call`
- [ ] 3.2 `openspec archive`
