## 1. 修复 ctoken 刷新

- [x] 1.1 在 `zm_auto/services/registrar_class.py` 的 CDP 登录分支，注入 cookies 后刷新 `self.ctoken`

## 2. 修复 CSRF token 提取

- [x] 2.1 在 `zm_auto/captcha/login_solver.py` 的 CSRF 提取逻辑中增加 `ctoken` 回退

## 3. 验证

- [x] 3.1 `python -m compileall zm_auto/`
- [ ] 3.2 CDP 登录注册测试，确认 `/api_key/create` 不再返回 `invalid csrf token`

## 4. OpenSpec

- [ ] 4.1 `openspec validate --changes fix-cdp-login-ctoken-csrf-refresh`
- [ ] 4.2 `openspec archive`
