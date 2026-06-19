# /opsx:apply — 实现 OpenSpec 变更

按 tasks.md 逐步实现当前 OpenSpec change。

对应项目内 Skill: `openspec-apply-change`

## 前置条件

- 必须已输出 Bridge Plan（使用 `openspec-superpowers-bridge`）
- 所有 applyRequires 工件必须已完成

## 执行

1. 读取 `openspec status --change "<name>" --json`
2. 读取所有 contextFiles（proposal、design、specs、tasks）
3. 按 tasks.md 顺序逐项实现，每完成一项勾选 `- [x]`
4. 保持改动最小化，只做当前 task 范围内的修改
