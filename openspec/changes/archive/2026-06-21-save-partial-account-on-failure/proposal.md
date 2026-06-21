## Why

当前注册流程在 API Key 创建失败时会直接抛异常，导致 `accounts.json` 中没有任何记录。但此时邮箱、user_id 等账号信息已经获取到，丢失这些信息不利于后续排查和复用。

## What Changes

- API Key 创建失败时不再直接抛异常
- 将已获取的账号信息（email、email_provider、email_token、user_id 等）与错误原因一并返回
- `accounts.json` 中增加 `note` 或 `error` 字段标识失败阶段

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `account-registration`: 注册失败时仍持久化部分账号信息到 `accounts.json`。

## Impact

- `zm_auto/services/registrar_class.py`
- `accounts.json` 输出结构增加 `note`/`error` 字段（仅在失败时）
