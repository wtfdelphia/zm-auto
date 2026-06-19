---
name: spec-compliance-check
description: Review an implemented change against its OpenSpec artifacts and project rules. Trigger after implementation or before code review.
---

# Spec Compliance Check

## Dimensions

| Dimension | Question |
| --- | --- |
| Scope | Are there out-of-scope changes? |
| Design | Does the implementation follow `design.md`? |
| Scenarios | Is every requirement covered by code/test evidence? |
| Project Rules | Does it respect `AGENTS.md` and `spec/`? |
| Verification | Are required verifications run and reported truthfully? |
| README/AGENTS Sync | Do entry files need updates? |

## Report Template

```markdown
## Spec Compliance Report: <change-name>

### Summary
| Dimension | Status | Notes |
| --- | --- | --- |
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

## Rule

CRITICAL items must be fixed or the specification updated before proceeding.
