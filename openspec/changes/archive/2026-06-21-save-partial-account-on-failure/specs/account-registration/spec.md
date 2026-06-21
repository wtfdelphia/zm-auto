## MODIFIED Requirements

### Requirement: 单个账号注册

用户 SHALL 通过 CLI 命令 `python -m zm_auto register -n 1` 完成单个账号的全自动注册流程。根目录保留 `register.py` 薄兼容入口，执行 `python register.py -n 1` 时委托给 `python -m zm_auto register -n 1`。

#### Scenario: API Key 创建失败时仍保存账号信息

- **WHEN** 注册流程已成功登录并获取到 `user_id`
- **AND** 后续创建 API Key 失败
- **THEN** 系统 SHALL 将已获取的邮箱、user_id 等信息写入 `accounts.json`
- **AND** 记录失败原因到 `note` 或 `error` 字段

## ADDED Requirements

无。

## REMOVED Requirements

无。
