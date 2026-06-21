## 1. 移除提前 logout

- [x] 1.1 在 `zm_auto/services/registrar_class.py` 的 CDP 分支中删除登录成功后的 `login_solver.logout()` 调用

## 2. 验证

- [x] 2.1 `python -m compileall zm_auto/`
- [ ] 2.2 CDP 注册测试，确认登录成功后能正常获取 user_info 和创建 API Key

## 3. OpenSpec

- [ ] 3.1 `openspec validate --changes fix-cdp-early-logout-invalidates-session`
- [ ] 3.2 `openspec archive`
