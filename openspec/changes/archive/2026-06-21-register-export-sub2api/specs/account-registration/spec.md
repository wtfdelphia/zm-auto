## ADDED Requirements

### Requirement: register 命令支持导出 sub2api 兼容文件

系统 SHALL 允许用户通过 `python -m zm_auto register --export-sub2api` 在注册成功后直接生成/追加 `sub2api_export.json`。

#### Scenario: 单账号注册后导出

- **WHEN** 用户执行 `python -m zm_auto register -n 1 --export-sub2api`
- **THEN** 系统注册 1 个账号
- **AND** 将账号信息以 sub2api 兼容格式追加到 `sub2api_export.json`
- **AND** 文件保持 `{"exported_at", "proxies", "accounts"}` 结构

#### Scenario: 多账号追加去重

- **WHEN** 用户执行 `python -m zm_auto register -n 5 --export-sub2api`
- **AND** 其中 3 个账号注册成功
- **THEN** 系统追加 3 条账号记录到 `sub2api_export.json`
- **AND** 已存在的 `api_key` 不会重复写入

#### Scenario: 不影响自动导入

- **WHEN** `config.json` 中 `sub2api.enabled=true`
- **AND** 用户执行 `python -m zm_auto register -n 1 --export-sub2api`
- **THEN** 系统仍然按原逻辑调用 Sub2API 导入
- **AND** 同时生成 `sub2api_export.json`

## MODIFIED Requirements

无。

## REMOVED Requirements

无。
