## 1. 修改注册流程

- [x] 1.1 在 `zm_auto/services/registrar_class.py` 中，API Key 创建失败时返回部分账号信息而不是抛异常
- [x] 1.2 返回 dict 中包含 `note` 字段，记录失败原因

## 2. 验证

- [x] 2.1 `python -m compileall zm_auto/`
- [ ] 2.2 模拟 API Key 创建失败场景，确认 `accounts.json` 中仍保存邮箱等信息

## 3. OpenSpec

- [ ] 3.1 `openspec validate --changes save-partial-account-on-failure`
- [ ] 3.2 `openspec archive`
