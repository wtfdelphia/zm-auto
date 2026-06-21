## 1. 修复 CDP 登录 `/verify?method=unknown` 检测逻辑

- [x] 1.1 修改 `zm_auto/captcha/login_solver.py` 中 `_wait_for_login_or_verify`，当 URL 为 `/verify?method=unknown` 时等待 15 秒后通过浏览器内 `/api/user/info` 判断登录状态。
- [x] 1.2 若 `/api/user/info` 返回有效 `data.userId`，即使 URL 仍在 `/verify?method=unknown`，也视为登录成功并返回。
- [x] 1.3 保持原有 `/` 或 `/platform` 跳转成功判定，不改变其他路径行为。

## 2. 修复 CDP 退出登录时序

- [x] 2.1 修改 `zm_auto/services/registrar_class.py` 的 `Registrar.close()`，移除 CDP 浏览器 logout 调用，仅关闭 HTTP session 与 solver。
- [x] 2.2 在 `Registrar` 中新增 `logout()` 方法，负责调用 `self._cdp_solver.logout()`。
- [x] 2.3 修改 `zm_auto/services/registrar.py` 的 `run()`，收集所有 `Registrar` 实例，在 `save_results()` 和 `_export_sub2api_json()` 完成后统一调用 `logout()`。
- [x] 2.4 确保 `run()` 在保存或导出异常时，仍尝试执行 logout。

## 3. 验证

- [x] 3.1 执行 `python -m compileall zm_auto/` 通过语法检查。
- [x] 3.2 执行 `python -m py_compile zm_auto/captcha/login_solver.py` 与 `zm_auto/services/registrar.py`。
- [ ] 3.3 执行 `python -m zm_auto register -n 1 --export-sub2api`（使用 CDP）测试完整流程。

## 4. OpenSpec

- [x] 4.1 运行 `openspec validate --changes fix-cdp-verify-detection-and-logout-timing`。
- [ ] 4.2 归档变更。
