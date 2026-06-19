---
name: openspec-superpowers-bridge
description: Convert an OpenSpec change into an executable Bridge Plan before implementation. Trigger before writing code for any OpenSpec change.
---

# OpenSpec Superpowers Bridge

## Required Inputs

- `AGENTS.md`
- `spec/design.md`
- `openspec/project.md`
- `openspec/changes/<name>/proposal.md`
- `openspec/changes/<name>/design.md`
- `openspec/changes/<name>/specs/**/spec.md` (if exists)
- `openspec/changes/<name>/tasks.md`

## Output Format

Produce a Bridge Plan in the conversation:

```markdown
## Bridge Plan: <change-name>

### Summary
- Scope:
- Non-goals:
- Key decisions:

### High-risk Items
- Config / secrets:
- Captcha / provider APIs:
- CLI / output contract:
- Target site behavior:

### Impact Evidence
- CodeGraph query:
- rg / source-reading notes:

### Task Mapping
| Task | Step | Test | Done |
| ... | ... | ... | ... |

### Required Verification
- python -m py_compile ...
- python <script> --help
- smoke test command

### Stop Conditions
- Missing artifacts
- Contradictory requirements
- New high-risk impact not in design
```

## Stop Conditions

- Any required artifact is missing
- `proposal.md` and `design.md` contradict each other
- New high-risk impact is discovered but not documented
