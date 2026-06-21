## 1. 修复退出登录线程错误

- [x] 1.1 修改 `Registrar.logout()`，使用 `curl_cffi.requests.post` 直接调用服务端 `/api/user/logout?ctoken=<ctoken>`。
- [x] 1.2 修改 `Registrar.close()`，在 worker 线程内关闭 `_cdp_solver`。
- [x] 1.3 确保 `logout()` 在 `self.ctoken` 为空或 `logout_after=false` 时不执行。

## 2. 验证

- [ ] 2.1 执行 `python -m compileall zm_auto/` 通过语法检查。
- [ ] 2.2 执行 `python -m zm_auto register -n 1 --export-sub2api`（CDP）确认不再出现 `cannot switch to a different thread` 错误。
- [ ] 2.3 确认 `accounts.json` / `sub2api_export.json` 写入后，日志出现“服务端退出登录”且无异常。

## 3. OpenSpec

- [ ] 3.1 运行 `openspec validate --changes fix-logout-thread-error`。
- [ ] 3.2 归档变更。
