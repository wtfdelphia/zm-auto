## 1. 修复端点与请求参数

- [x] 1.1 修正 `ZenmuxAdapter.register_endpoints()` 中 `create_key` 端点为 `/api/api_key/create`
- [x] 1.2 在 `_post_via_page()` 中增加 `ctoken` 参数，并把 `ctoken` 附加到 URL 查询参数
- [x] 1.3 在 `create_api_key()` 调用 `_post_via_page()` 时传入 `ctoken`
- [x] 1.4 将创建 API Key 的 payload `tags` 默认值从 `[]` 改为 `["free"]`

## 2. 验证

- [x] 2.1 运行 `python -m py_compile` 检查修改文件语法
- [x] 2.2 运行 `python -m zm_auto user-info --help` 确认 CLI 加载正常
- [x] 2.3 运行 `python -m zm_auto user-info --create-key` 验证可正确创建并返回完整 API Key

## 3. OpenSpec 归档

- [x] 3.1 创建 proposal.md
- [x] 3.2 创建 specs/
- [x] 3.3 创建 design.md
- [x] 3.4 创建 tasks.md
- [ ] 3.5 运行 `openspec verify-change` 并通过
- [ ] 3.6 运行 `openspec archive-change` 归档
