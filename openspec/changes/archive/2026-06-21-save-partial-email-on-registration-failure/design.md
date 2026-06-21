## Context

`Registrar.register()` 在注册过程中抛出异常时，`worker()` 只返回 `{"ok": False, "error": ...}`，没有任何结果数据。`save_results()` 只保存 `ok=True` 的结果。

## Goals / Non-Goals

**Goals:**
- 失败时保存已创建的邮箱信息
- 失败记录中包含错误原因

**Non-Goals:**
- 不改变成功记录的格式
- 不修改 CLI 参数

## Decisions

1. 在 `worker()` 的 `except` 块中访问 `registrar.mailbox`，构造 partial result
2. `save_results()` 保存所有带有 `result` 的记录，无论 `ok` 状态
3. 失败记录的 `api_key` 为空，`error` 为异常信息

## Risks / Trade-offs

- `accounts.json` 中可能出现大量失败记录，但有利于排查
- 失败记录没有 `user_id`、`api_key` 等字段，下游解析需要注意
