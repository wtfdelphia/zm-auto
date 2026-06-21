## 1. 修改 CDP 登录成功 URL 判断

- [x] 1.1 在 `zm_auto/captcha/login_solver.py` 的 `_wait_for_login_or_verify()` 中把 `/` 也视为登录成功

## 2. 验证

- [x] 2.1 `python -m py_compile zm_auto/captcha/login_solver.py`
- [x] 2.2 `python -m compileall zm_auto/`
- [ ] 2.3 CDP 登录测试：额外验证完成后跳转到 `/`，登录流程成功

## 3. OpenSpec

- [ ] 3.1 `openspec validate --changes fix-cdp-login-success-root-url`
- [ ] 3.2 `openspec archive`
