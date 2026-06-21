## 1. 修改 worker 和 save_results

- [x] 1.1 在 `zm_auto/services/registrar.py` 的 `worker()` except 块中构造 partial result
- [x] 1.2 修改 `save_results()` 保存所有带 `result` 的记录

## 2. 验证

- [x] 2.1 `python -m compileall zm_auto/`
- [ ] 2.2 模拟注册失败，确认 `accounts.json` 中保存了邮箱信息

## 3. OpenSpec

- [ ] 3.1 `openspec validate --changes save-partial-email-on-registration-failure`
- [ ] 3.2 `openspec archive`
