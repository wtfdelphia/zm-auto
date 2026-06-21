## 1. 修复 logout HTTP 500

- [x] 1.1 `Registrar.close()` 不再关闭 HTTP session。
- [x] 1.2 `Registrar.logout()` 使用 `self.session` 发起 POST，带上 session cookies。
- [x] 1.3 `Registrar.logout()` 若 `csrf_token` 存在则添加 CSRF 请求头。
- [x] 1.4 `Registrar.logout()` 退出后关闭 session。

## 2. 验证

- [ ] 2.1 `python -m compileall zm_auto/` 通过。
- [ ] 2.2 `python -m zm_auto register -n 1 --export-sub2api`（CDP）确认退出登录返回 2xx，无 HTTP 500。

## 3. OpenSpec

- [ ] 3.1 `openspec validate --changes fix-logout-http-500`。
- [ ] 3.2 归档变更。
