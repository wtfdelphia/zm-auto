## Context

`register` 命令通过 `Registrar.register()` 完成单个账号注册，返回包含 `email`、`user_id`、`api_key`、`key_name` 的字典。`services/registrar.py` 的 `run()` 汇总结果后保存到 `accounts.json`。

`user-info --export-sub2api` 已经提供了导出 `sub2api_export.json` 的能力，入口是 `zm_auto.services.user_info.export.export_sub2api(result, output_path)`。该函数支持按 `api_key` 去重追加。

## Goals / Non-Goals

**Goals:**
- 在 `register` 命令增加 `--export-sub2api` 和 `--export-sub2api-output`
- 多账号注册成功后，把结果追加到 `sub2api_export.json`
- 复用现有 `export_sub2api()` 的去重与格式逻辑

**Non-Goals:**
- 不改动 `sub2api.enabled=true` 时的自动导入逻辑
- 不修改 `user-info` 命令行为
- 不新增配置项

## Decisions

1. **复用 `export_sub2api()`**
   - 该函数已经实现了 sub2api 兼容格式、追加、去重。
   - 需要构造与 `user-info` 输出一致的 `result` 字典：`api_keys` 列表 + `user_info` 字典。

2. **多账号一次性追加**
   - `Registrar.register()` 返回的 `user_id` 可用于构造 `user_info.userId`。
   - `export_sub2api()` 接受单个 `result`，但每次调用都会读取并重新写入整个文件。
   - 为了避免多次读写大文件，可以在所有 worker 完成后汇总所有成功账号，构造一个 `result` 调用一次 `export_sub2api()`。

3. **不改动自动导入**
   - `registrar_class.py` 中的 `Sub2APIImporter.import_key()` 保持原样。
   - `--export-sub2api` 是新增的可选导出行为，与导入逻辑独立。

## Risks / Trade-offs

- **accounts.json 与 sub2api_export.json 信息不一致**：如果后续 `export_sub2api()` 的格式升级，register 的构造逻辑也需要同步。
- **大文件追加性能**：当 `sub2api_export.json` 非常大时，每次读取重写会有性能开销。当前场景下账号量可控，可接受。

## Migration Plan

无需迁移。新增 `--export-sub2api` 为可选参数，默认行为不变。
