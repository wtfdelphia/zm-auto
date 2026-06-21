# user-info Specification

## Purpose
TBD - created by archiving change fix-user-info-api-key-creation. Update Purpose after archive.
## Requirements
### Requirement: user-info 命令支持自动创建 API Key

当 Chrome CDP 会话已登录且当前账号没有可用 API Key 时，系统 SHALL 支持通过 `--create-key` 自动调用目标站点接口创建 API Key，并返回完整 token。

#### Scenario: 无 key 时自动创建成功

- **WHEN** 用户执行 `python -m zm_auto user-info --create-key`
- **AND** 目标站点 API Key 创建端点为 `/api/api_key/create`
- **THEN** 系统向该端点发送包含 `name` 和 `tags` 的 POST 请求
- **AND** 请求 URL 包含 `ctoken` 查询参数
- **AND** 系统从响应 `{success, data: {token, ...}}` 中提取完整 API Key
- **AND** 结果写入 `user_info.json`

#### Scenario: 已有 key 时直接读取

- **WHEN** 用户执行 `python -m zm_auto user-info --create-key`
- **AND** 页面已存在有效 API Key
- **THEN** 系统直接读取现有 API Key，不再重复创建

