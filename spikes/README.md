# Spikes

A spike is exploratory code written to answer one specific question, such as "can library X parse these attachments?" or "how fast is model Y on our hardware?". Spikes are throwaway by design.

## Rules
- **One folder per question:** `spikes/NNN-short-name/`, numbered in order.
- **Every spike has a `README.md`** that states the question up front. When the spike is finished, add the answer (and the evidence for it) to the same README.
- **Tests are not required.** Spike code is for learning, not for shipping.
- **Spike code never leaves `spikes/`.** It is never imported by or copied into `backend/` or `frontend/`.
- **Keeping an idea means rebuilding it.** If a spike's idea is worth keeping, it gets a spec in `specs/NNN-short-name/` and is rebuilt properly, with tests, following the [Testing policy](../CLAUDE.md#testing-policy).

The project's data guardrails still apply inside spikes: no raw comment data or secrets in the repo, no holdout data, and comment data goes only to approved model endpoints (see "Feasibility-phase guardrails" in [CLAUDE.md](../CLAUDE.md)).

## Spike README template
```markdown
# NNN: Short name

**Question:** the one question this spike answers.

**Status:** in progress | answered | abandoned

**Answer:** (fill in when finished) the answer, with the evidence: what was run, on what inputs, and the measured results.

**Next step:** drop it, or write a spec to rebuild it properly.
```
