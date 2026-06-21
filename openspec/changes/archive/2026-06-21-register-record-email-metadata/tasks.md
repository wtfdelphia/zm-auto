## 1. 注册结果增加字段

- [x] 1.1 在 `zm_auto/services/registrar_class.py` 的 `register()` 返回字典中增加 `email_provider` 和 `email_token`
- [x] 1.2 从 `self.mailbox` 读取 `provider` 和 `token`，缺失时置为空字符串

## 2. 验证

- [x] 2.1 `python -m py_compile` 检查修改文件语法
- [ ] 2.2 运行注册命令，确认 `accounts.json` 中出现 `email_provider` 和 `email_token`
- [ ] 2.3 多账号注册时确认每个账号字段独立

## 3. OpenSpec

- [ ] 3.1 `openspec validate --changes register-record-email-metadata` 通过
- [ ] 3.2 `openspec archive` 归档
