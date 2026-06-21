## Context

`Registrar.register()` 在最后创建 API Key 时：

```python
if not api_key:
    raise RuntimeError(f"创建 API Key 失败: {create_resp}")
```

这导致 worker 返回 `{"ok": False}`，结果不会被写入 `accounts.json`。

## Goals / Non-Goals

**Goals:**
- 在 API Key 创建失败时保存已有账号信息
- 保留错误信息便于排查

**Non-Goals:**
- 不隐藏真实错误
- 不改变成功时的输出结构

## Decisions

1. 将 API Key 创建逻辑包在 try/except 中
2. 失败时返回包含部分信息的 dict，并带 `note` 字段
3. `note` 字段示例：`"api_key_create_failed: invalid csrf token"`

## Risks / Trade-offs

- `accounts.json` 中会出现未完全成功的账号，下游处理时需要注意 `note` 字段
