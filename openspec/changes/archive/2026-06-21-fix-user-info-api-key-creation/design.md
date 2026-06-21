## Context

`zm_auto/services/user_info/core.py` 中的 `create_api_key()` 通过 `ZenmuxAdapter.register_endpoints()` 获取 API Key 创建端点。当前 adapter 返回 `/api/api_key`，这不是创建端点，导致响应中没有完整 token，回退到 list/DOM 抓取也失败。

目标站点的正确调用为：

```
POST https://zenmux.ai/api/api_key/create?ctoken=<ctoken>
{"name":"...","tags":["free"]}
```

响应：

```json
{"success": true, "data": {"id": "...", "name": "...", "token": "sk-ai-..."}}
```

## Goals / Non-Goals

**Goals:**
- 让 `user-info --create-key` 能正确创建并获取完整 API Key
- 保持 `_post_via_page` 与 `_post_via_http` 在 `ctoken` 处理上行为一致
- 使用与目标站点兼容的 `tags` 默认值

**Non-Goals:**
- 不改动 `user-info` CLI 参数或输出格式
- 不改动 sub2api 导出逻辑
- 不新增配置项

## Decisions

1. **端点修正**：`zenmux.py` 中 `create_key` 改为 `/api/api_key/create`
   - 这是最直接、最小侵入的修复，与 `api_key/list` 保持同一前缀风格。

2. **`_post_via_page` 增加 `ctoken` 参数**：与 `_post_via_http` 一致，在 URL 中附加 `?ctoken=...`
   - 目标站点要求 ctoken 在查询参数中，仅依赖浏览器自动 cookie 不够。

3. **`tags` 默认值改为 `["free"]`**
   - 与已验证的成功请求保持一致，避免空 tags 导致服务端行为不确定。

## Risks / Trade-offs

- **硬编码 `tags`**: `["free"]` 是站点特定的。未来如果站点对 tags 有变化，可能需要改为配置项。当前为最小修复，暂不引入配置。
- **provider 间差异**: 该修复针对 `zenmux` adapter，不影响其他潜在 adapter。

## Migration Plan

无需迁移。修复后重新执行 `python -m zm_auto user-info --create-key` 即可。
