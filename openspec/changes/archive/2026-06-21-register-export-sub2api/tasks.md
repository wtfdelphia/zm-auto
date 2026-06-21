## 1. CLI 参数

- [x] 1.1 在 `zm_auto/cli/commands.py` 的 `register` 命令中增加 `--export-sub2api` 和 `--export-sub2api-output` 参数
- [x] 1.2 在 `zm_auto/cli/register.py` 中接收并透传参数到 `run()`

## 2. 注册服务导出逻辑

- [x] 2.1 在 `zm_auto/services/registrar.py` 的 `run()` 中增加 `export_sub2api` 和 `export_sub2api_output` 参数
- [x] 2.2 汇总所有成功注册结果，为每个账号构造 `result = {"api_keys": [...], "user_info": {...}}`
- [x] 2.3 调用 `_save_sub2api_json()` 完成追加导出，不触发服务器导入

## 3. 验证

- [x] 3.1 `python -m zm_auto register --help` 显示新增参数
- [x] 3.2 `python -m py_compile` 检查修改文件语法
- [ ] 3.3 运行注册命令带 `--export-sub2api`，确认 `sub2api_export.json` 生成/追加
- [ ] 3.4 确认 `sub2api.enabled=true` 时仍自动导入服务器

## 4. OpenSpec

- [ ] 4.1 `openspec validate --changes register-export-sub2api` 通过
- [ ] 4.2 `openspec archive` 归档
