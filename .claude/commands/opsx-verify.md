# /opsx:verify — 验证 OpenSpec 变更

归档前验证实现与工件的一致性。

对应项目内 Skill: `openspec-verify-change`

## 执行

1. 读取 `openspec status --change "<name>" --json`
2. 验证三个维度：
   - Completeness: tasks 是否全部完成，Requirement 是否有实现
   - Correctness: 实现是否符合需求和场景意图
   - Coherence: 实现是否遵守 design 和项目模式
3. 输出 Verification Report
