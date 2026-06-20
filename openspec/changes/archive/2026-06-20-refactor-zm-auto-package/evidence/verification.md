# Verification Evidence

> 本目录存放 `refactor-zm-auto-package` 变更的验证证据。
> 请在实现阶段逐步补充各项验证结果。

## 静态检查

- [ ] `python -m compileall zm_auto/` 输出无错误
- [ ] `ruff check zm_auto/` 退出码为 0
- [ ] `mypy zm_auto/` 核心公共 API 无类型错误

## 测试

- [ ] `python -m pytest tests/ -v` 108 个测试全部 PASSED

## CLI 帮助

- [ ] `python -m zm_auto --help`
- [ ] `python -m zm_auto register --help`
- [ ] `python -m zm_auto user-info --help`
- [ ] `python -m zm_auto account-status --help`

## 兼容入口

- [ ] `python register.py --help`
- [ ] `python read_user_info.py --help`
- [ ] `python check_account_status.py --help`

## 冒烟验证

- [ ] `python -m zm_auto register -n 1` 完成一次完整注册流程
- [ ] `python -m zm_auto user-info --create-key` 成功读取/导出用户信息

## CDP 模式验证

- [ ] 配置 `captcha.provider = "cdp"` 后完成一次注册，确认 CDP 连接、页面导航、cookie 提取正常

## Spec Compliance

- [ ] `spec-compliance-check` 通过
- [ ] `openspec-verify-change` 通过
- [ ] `verification-before-completion` 通过
