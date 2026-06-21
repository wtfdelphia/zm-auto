## Why

当前注册失败时，`accounts.json` 不会写入任何记录。但即使注册失败，临时邮箱、provider、token 等信息已经产生，应该被保存下来，方便用户排查失败原因或复用邮箱。

## What Changes

- 当 `Registrar.register()` 抛出异常时，`worker()` 构造包含邮箱信息的 partial result
- `save_results()` 将成功和失败结果都追加到 `accounts.json`
- 失败记录中包含 `error` 字段说明失败原因

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `account-registration`: 扩展注册失败时的输出行为。

## Impact

- `zm_auto/services/registrar.py`
- `accounts.json` 输出结构变化（失败记录增加 `error` 字段）
