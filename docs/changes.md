当前工作区有 3 个变更项需要被 OpenSpec 跟踪。下面是梳理：

---

## 当前工作区状态

```bash
git status --short
 M zm_auto/services/user_info/cdp_export.py
 M zm_auto/services/user_info/core.py
 M zm_auto/sites/zenmux.py
```

这 3 个文件是我已经修改的 bug 修复代码，但还没有对应的 OpenSpec change。

`openspec list --json` 返回 `{"changes":[]}`，说明当前没有任何 OpenSpec change。

---

## 建议拆分的 3 个变更项

### Change 1: `fix-user-info-api-key-creation`

**类型**: 高优先级 bug 修复（代码已改，缺 OpenSpec 工件）

**问题**: `python -m zm_auto user-info --create-key` 调用的是 `/api/api_key`，而正确端点是 `/api/api_key/create`，导致创建后拿不到完整 `token`，最终 `api_keys` 为空。

**已修改代码**:
- `zm_auto/sites/zenmux.py`: `create_key` 端点改为 `/api/api_key/create`
- `zm_auto/services/user_info/cdp_export.py`: `_post_via_page` 增加 `ctoken` 参数，URL 附加 `ctoken`
- `zm_auto/services/user_info/core.py`: 调用时传入 `ctoken`；payload `tags` 改为 `["free"]`

**待补**: 验证命令、OpenSpec 工件（proposal/design/tasks）、归档。

---

### Change 2: `register-export-sub2api`

**类型**: 功能增强（CLI 参数变化 + 输出行为变化）

**需求**: `python -m zm_auto register` 增加 `--export-sub2api` 能力，注册成功后直接生成 `sub2api_export.json`，不需要再跑一遍 `user-info --export-sub2api`。

**影响面**:
- `zm_auto/cli/commands.py`: `register` 命令增加 `--export-sub2api`、`--export-sub2api-output`
- `zm_auto/cli/register.py`: 接收并透传参数
- `zm_auto/services/registrar.py`: 汇总结果，调用 `export_sub2api()`
- `zm_auto/services/registrar_class.py`: 当前 `sub2api.enabled=true` 时直接 `Sub2APIImporter.import_key()`，需要处理与 `--export-sub2api` 的重复导入问题

**设计选择**:
- 方案 A: `--export-sub2api` 仅导出 JSON，不影响现有自动导入逻辑
- 方案 B: 统一走 `export_sub2api()`，移除 register 里的直接导入逻辑，让行为与 `user-info` 一致

**风险**: 多账号追加写入、与现有 `sub2api.enabled` 自动导入的重复问题。

**依赖 spec**: 需要更新 `openspec/specs/account-registration/spec.md` 和 `openspec/specs/cli-interface/spec.md`。

---

### Change 3: `register-record-email-metadata`

**类型**: 输出格式变化

**需求**: `accounts.json` 增加邮箱 provider 类型和对应的 JWT，例如：

```json
{
  "email": "wtfmugaim0@delphiedu.com",
  "email_provider": "duckmail",
  "email_token": "eyJhbGciOiJIUzI1Ni...",
  "user_id": "...",
  "api_key": "..."
}
```

**影响面**:
- `zm_auto/services/registrar_class.py`: 在 `return {...}` 中增加 `email_provider` 和 `email_token` 字段
- 邮箱 provider 的 `create_mailbox()` 已经返回 `provider` 和 `token`，多数情况下可以直接复用

**风险**:
- `accounts.json` 结构变化，下游解析脚本需要同步
- 不同 provider 返回的 `token` 含义/有效期不一致（`gptmail` 甚至不返回 `token`）
- 敏感信息本地明文存储（虽然 `accounts.json` 已在 `.gitignore`）

**依赖 spec**: 需要更新 `openspec/specs/account-registration/spec.md`。

---

## 变更项关系

```
                    ┌─────────────────────────────┐
                    │  fix-user-info-api-key-creation  │
                    │     (bug 修复，已改代码)        │
                    └─────────────────────────────┘
                                  │
                    独立，可单独验证/归档

        ┌─────────────────────────┐
        │ register-export-sub2api  │
        │    (CLI + 输出行为)      │
        └─────────────────────────┘
                    │
        可独立实施，但可能和 Change 3 同时改到 accounts.json 输出

        ┌─────────────────────────────┐
        │ register-record-email-metadata│
        │    (accounts.json 加字段)    │
        └─────────────────────────────┘
```

**分组建议**:
- Change 1 单独作为一个 change，高优先级，先归档
- Change 2 和 Change 3 可以各自独立成 change，也可以合并为 `register-output-enhancements`；我建议分开，因为一个是导出行为，一个是输出字段，验证方式不同

---

## 下一步建议

1. **先处理 Change 1（bug 修复）**: 因为它已经改完代码，只需要补 OpenSpec 工件、验证、归档，最快闭环。
2. **然后创建 Change 2 和 Change 3**: 走 `openspec-new-change` 或 `openspec-propose`，产出 proposal/design/tasks。
3. **同步更新长期 specs**: `account-registration` 和 `cli-interface` 都需要更新。

你是否要我继续：
- **A.** 先为 Change 1 创建 OpenSpec 变更工件并推进归档？
- **B.** 同时为 3 个 change 批量创建 OpenSpec 变更工件？
- **C.** 继续深入某个 change 的设计细节？