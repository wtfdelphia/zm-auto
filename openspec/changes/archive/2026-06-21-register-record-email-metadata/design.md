## Context

`Registrar.register()` 在创建临时邮箱后已经提取了 `provider` 和 `token`：

```python
self.mailbox = create_mailbox(...)
email = str(self.mailbox.get("address") or "").strip()
jwt = str(self.mailbox.get("token") or "").strip()
```

但返回结果时没有把 `provider` 和 `token` 持久化到 `accounts.json`。

## Goals / Non-Goals

**Goals:**
- 将 `email_provider` 和 `email_token` 加入每个成功账号的输出记录
- 多账号时每个账号独立记录自己的 provider 和 token

**Non-Goals:**
- 不新增 CLI 参数
- 不修改 `sub2api_export.json` 结构
- 不修改 provider 返回值约定

## Decisions

1. **字段命名**
   - 使用 `email_provider` 和 `email_token`，语义清晰，避免与 zenmux session JWT 混淆。

2. **数据来源**
   - `email_provider` 取 `self.mailbox.get("provider")` 或 `self.mailbox.get("provider_ref")` 的 readable 名称
   - `email_token` 取 `self.mailbox.get("token")`，缺失时为空字符串

3. **多账号支持**
   - `accounts.json` 已经是数组，`save_results()` 逐条追加，天然支持多账号。
   - 只需在 `Registrar.register()` 返回的 dict 中补充字段即可。

## Risks / Trade-offs

- `accounts.json` 结构变化，下游解析脚本需要适配。
- `email_token` 是敏感信息，但 `accounts.json` 已在 `.gitignore` 中。
- 不同 provider 的 `token` 有效期/权限不同，文档需要说明这是邮箱 provider token。
