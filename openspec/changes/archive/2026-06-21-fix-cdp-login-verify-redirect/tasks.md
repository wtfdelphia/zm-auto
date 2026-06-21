## 1. 修改 CDP 登录流程

- [x] 1.1 在 `zm_auto/captcha/login_solver.py` 中，填写验证码后改为等待 URL 跳转
- [x] 1.2 处理 `/verify?method=unknown` 后至少等待 15 秒
- [x] 1.3 保留点击按钮作为 fallback，但不再强依赖

## 2. 验证

- [x] 2.1 `python -m py_compile zm_auto/captcha/login_solver.py`
- [x] 2.2 `python -m compileall zm_auto/`
- [ ] 2.3 CDP 登录测试：输入验证码后自动跳转 `/verify?method=unknown`，最终到达 `/platform`

## 3. OpenSpec

- [ ] 3.1 `openspec validate --changes fix-cdp-login-verify-redirect`
- [ ] 3.2 `openspec archive`
