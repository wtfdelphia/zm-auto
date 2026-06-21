## Why

目前 `accounts.json` 只记录 `email`、`user_id`、`api_key`、`key_name`、`created_at`。用户无法从注册结果中知道该账号使用了哪个邮箱 provider，也拿不到邮箱 provider 的访问 token，后续排查或复用账号时缺少上下文。

## What Changes

- 在 `accounts.json` 每条记录中增加 `email_provider` 和 `email_token` 字段
- 字段从 `create_mailbox()` 返回的 `provider` 和 `token` 中提取
- 多账号注册时，每个成功账号各自写入对应的邮箱 provider 和 token
- 对于不返回 `token` 的 provider，`email_token` 为空字符串

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `account-registration`: 扩展注册结果输出字段。

## Impact

- `zm_auto/services/registrar_class.py`
- `accounts.json` 输出结构变化
- 不修改 CLI 参数
