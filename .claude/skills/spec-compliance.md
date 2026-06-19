# Spec Compliance Check Skill

## 触发条件

实现完成后、代码审查前后、归档前。

## 审查维度

| 维度 | 核心问题 |
|------|---------|
| Scope | 有没有实现范围外功能，违反非目标，改无关模块 |
| Design | 是否遵守 design.md 的技术决策 |
| Scenarios | 每个 Requirement / Scenario 是否有实现和测试证据 |
| Project Rules | 是否符合 AGENTS.md 和 spec/ 的长期规则 |
| Verification | 是否有匹配高风险类型的验证命令和结果 |
| README/AGENTS Sync | README、AGENTS、spec、openspec/specs 是否需要更新 |

## 报告模板

```markdown
## Spec Compliance Report: <change-name>

### Summary
| Dimension | Status | Notes |
|-----------|--------|-------|
| Scope | PASS/WARN/FAIL | ... |
| Design | PASS/WARN/FAIL | ... |
| Scenarios | PASS/WARN/FAIL | ... |
| Project Rules | PASS/WARN/FAIL | ... |
| Verification | PASS/WARN/FAIL | ... |
| README/AGENTS Sync | PASS/WARN/FAIL | ... |

### CRITICAL
- ...

### WARNING
- ...

### Evidence
- Files read:
- Tests run:
```

CRITICAL 项必须修复或更新规格后重新审查。
