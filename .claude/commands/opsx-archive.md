# /opsx:archive — 归档 OpenSpec 变更

归档已完成变更，同步 delta specs 到长期 specs。

对应项目内 Skill: `openspec-archive-change`

## 前置条件

- tasks.md 全部完成
- 已通过 spec-compliance-check
- 已通过 openspec-verify-change
- 已通过 verification-before-completion

## 执行

1. 检查工件和任务完成状态
2. 评估 delta spec 同步状态
3. 执行归档：`openspec archive <name>`
4. 同步 README/AGENTS/spec 判断
