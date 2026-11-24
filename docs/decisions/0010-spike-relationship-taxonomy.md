# ADR 0010: Spike relationship taxonomy and how it maps to the app model

- **Status:** Proposed
- **Date:** 2026-11-24
- **Register:** TX-01, TX-02, TX-03, TX-07

## Context
The spike labels pairs with the six-label taxonomy in SiLab §7.5: `EQUIVALENT`, `DIRECT_CONFLICT`, `PARTIAL_OR_QUALIFIED_CONFLICT`, `RELATED_COMPATIBLE`, `UNRELATED`, `INDETERMINATE`. The app model in §4.5 has about 20 relationship types. §10 forbids silently redefining claim and recommendation semantics or the evidence-status taxonomy.

## Decision
- **TX-01:** The spike keeps the six labels. Each §4.5 type is recovered later from a label plus a `proposition_kind` field (claim or recommendation) and a `subtype` attribute, using the mapping below.
- **TX-02:** Recommendation `JUSTIFIED_BY` claim is evaluated **within a comment only**, captured at extraction when the commenter states the premise. Cross-comment justification is deferred until after the gate.
- **TX-03:** The evidence relationships evaluated are evidence status (§4.6) and the within-comment `CITED_AS_SUPPORT_FOR` link. Finding-to-finding comparisons (`POTENTIALLY_INCONSISTENT_WITH`) are deferred.
- **TX-07:** Spike pair labels are symmetric. Directional types (`REFINES`, `JUSTIFIED_BY`) come after the gate.

| §4.5 type | Proposition kind | §7.5 spike label | Subtype |
| --- | --- | --- | --- |
| `EQUIVALENT_TO` | claim or recommendation | `EQUIVALENT` | — |
| `CONTRADICTS` | claim | `DIRECT_CONFLICT` | — |
| `QUALIFIES` (disagreement over a sub-scope) | claim | `PARTIAL_OR_QUALIFIED_CONFLICT` | `qualifies` |
| `QUALIFIES` (narrows without disagreeing) | claim | `RELATED_COMPATIBLE` | `qualifies` |
| `RELATED_TO` | claim | `RELATED_COMPATIBLE` | — |
| `CONFLICTS_WITH` | recommendation | `DIRECT_CONFLICT` | — |
| `PARTIALLY_CONFLICTS_WITH` | recommendation | `PARTIAL_OR_QUALIFIED_CONFLICT` | — |
| `ALTERNATIVE_TO` (cannot be adopted together) | recommendation | `DIRECT_CONFLICT` | `alternative` |
| `ALTERNATIVE_TO` (can be adopted together) | recommendation | `RELATED_COMPATIBLE` | `alternative` |
| `REFINES` | recommendation | `RELATED_COMPATIBLE` | `refines` |

## Consequences
- A small, well-defined label set improves annotator agreement and gives clearer metrics (SiLab §9.4).
- The two split rows (`QUALIFIES`, `ALTERNATIVE_TO`) are where annotators will most likely disagree. The rubric needs paired examples for each.
- Directional and cross-comment relationships aren't measured by the spike. A "go" doesn't show they are feasible.

## Alternatives considered
- Expanding the spike taxonomy to the full §4.5 set: too many labels to annotate reliably in a 1–2 week spike.
