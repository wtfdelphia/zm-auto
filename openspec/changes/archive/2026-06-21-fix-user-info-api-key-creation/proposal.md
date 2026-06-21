## Why

`python -m zm_auto user-info --create-key` 在自动创建 API Key 时调用的是错误的端点 `/api/api_key`，导致响应中没有完整 `token`，最终 `api_keys` 为空。这直接破坏了 `user-info` 命令自动创建 API Key 的能力，也影响了 `--export-sub2api` 导出 0 个账号的后续问题。

## What Changes

- 修正 `ZenmuxAdapter.register_endpoints()` 中 `create_key` 端点：`/api/api_key` → `/api/api_key/create`
- 在 `_post_via_page()` 中支持通过 `ctoken` 参数把 `ctoken` 附加到 URL 查询参数，与 `_post_via_http()` 保持一致
- 在 `create_api_key()` 调用 `_post_via_page()` 时传入 `ctoken`
- 将创建 API Key 的 payload `tags` 默认值从 `[]` 改为 `["free"]`，与目标站点实际接受的请求格式一致

## Capabilities

### New Capabilities

- `user-info`: 定义 `user-info` 命令读取已登录账号信息、自动创建 API Key 的行为。

### Modified Capabilities

无。此变更仅修复现有 `user-info` 命令中 API Key 自动创建的实现缺陷，不改变其他 capability 的行为要求。

## Impact

- `zm_auto/sites/zenmux.py`
- `zm_auto/services/user_info/cdp_export.py`
- `zm_auto/services/user_info/core.py`
- 不修改 CLI 参数、配置文件结构或输出格式
