## Tasks

- [x] 修改 `zm_auto/captcha/login_solver.py` 中 `_wait_for_login_or_verify`：
  - 在 `/verify?method=unknown` 页面进入轮询 `/api/user/info`。
  - 仅当 `data.userId`/`data.accountId` 存在 **且** `data.needVerify` 为 `false` 时视为成功。
  - `needVerify` 为 `true` 时继续等待，超时抛错。
  - 增强日志，输出每次 `needVerify` 值。
- [x] 同步更新 `openspec/specs/captcha-provider/spec.md` 中 `/verify?method=unknown` 的判定要求。
- [x] 运行语法检查：`python -m py_compile zm_auto/captcha/login_solver.py`。
- [x] 优化验证码输入框等待时间：从 30s 缩短为 5s，减少无输入框时的空等。
- [x] 移除/保护无验证按钮时会直接抛错的“点击验证...”步骤，改为只在 fallback 中尝试点击按钮，找不到时继续等待页面自动跳转。
- [x] 运行真实注册测试：`python -m zm_auto register -n 1 --export-sub2api`（captcha.provider=cdp），观察 `/verify?method=unknown` 日志确认成功后再创建 API Key。
- [x] 补充自动化测试：`tests/test_login_solver.py` 覆盖 `/verify?method=unknown` 的多种场景。
- [ ] 归档本变更。
