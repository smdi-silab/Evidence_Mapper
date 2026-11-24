# Specs: how we build features

Every feature moves through the same steps. Nothing gets built until it has an approved spec.

| Step | File | Who writes it | Done when |
|------|------|---------------|-----------|
| 1. Define | `spec.md` | You (Claude can draft) | You've reviewed it and set Status to Approved |
| 2. Plan | `plan.md` | Claude drafts from the spec | You've reviewed and approved it |
| 3. Break down | `tasks.md` | Claude drafts from the plan | You've approved it |
| 4. Build | code + tests | Claude, one task at a time | All tasks checked, all ACs tested |
| 5. Close | update status | Claude | Spec Status set to Implemented, docs updated |

## Starting a new feature
1. Pick the next number and a short name, e.g. `002-evidence-upload`.
2. Create the branch: `git checkout -b feat/002-evidence-upload`
3. Copy the templates: `cp -r specs/_templates specs/002-evidence-upload`
4. Write (or have Claude draft) `spec.md`.

## Example prompts for Claude Code
- "Draft spec 002 for evidence upload. Ask me questions first about anything unclear."
- "Read specs/002-evidence-upload/spec.md and draft plan.md. Don't write code yet."
- "Plan approved. Draft tasks.md."
- "Implement the next unchecked task in specs/002-evidence-upload/tasks.md."
- "Review the implementation of spec 002 against its acceptance criteria. What's missing?"

## Numbering
- `001`–`099`: features and foundation work, in the order they're started.
- Specs are never deleted. If a feature is dropped, set its Status to Abandoned and note why.
