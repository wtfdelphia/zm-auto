## Why

目前 `python -m zm_auto register` 只输出 `accounts.json`。用户若想要 `sub2api_export.json`，必须再执行一次 `python -m zm_auto user-info --export-sub2api`。注册流程已经拿到所有必要字段，应该能直接导出 sub2api 兼容格式，减少一步操作。

## What Changes

- 给 `python -m zm_auto register` 增加 `--export-sub2api` 参数
- 注册成功后，将本次注册的账号按 sub2api 兼容格式追加写入 `sub2api_export.json`
- 多账号/多并发时，所有成功账号一次性追加到同一文件，按 `api_key` 去重
- 保留现有 `sub2api.enabled=true` 时的自动导入逻辑，不产生影响

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `account-registration`: 增加注册后可选导出 `sub2api_export.json` 的行为。

## Impact

- `zm_auto/cli/commands.py`
- `zm_auto/cli/register.py`
- `zm_auto/services/registrar.py`
- `zm_auto/services/registrar_class.py`（可能需要提供注册结果中的用户信息给导出函数）
- 不修改现有 `sub2api.enabled=true` 的自动导入路径
