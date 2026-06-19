---
name: verification-before-completion
description: Final verification gate before completing a change, PR, archive, or final response. Trigger at the end of every implementation session.
---

# Verification Before Completion

## Rules

- Only report commands that were actually run in this session.
- Do not use "should pass" as a substitute for "passed".
- Do not hide failed commands.
- Never paste real tokens, passwords, cookies, or sensitive reports.
- Run `git status --short` before final response to ensure no secrets or build artifacts are staged.

## Final Report Template

```markdown
## Verification

- `<command>`: PASS/FAIL/SKIPPED — result or reason

## Documentation Sync

- README.md: UPDATED / NOT NEEDED / SKIPPED — reason
- AGENTS.md: UPDATED / NOT NEEDED / SKIPPED — reason
- spec/: UPDATED / NOT NEEDED / SKIPPED — reason
- openspec/specs/: UPDATED / NOT NEEDED / SKIPPED — reason

## Residual Risk
- ...
```

## Stop Condition

- Critical verification is missing without explicit reason and residual risk
