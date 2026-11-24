# Regulatory Evidence Mapper — Decision Register

Nov 24, 2026 · @Tony

## How to use this register

This register lists the decisions that must be settled before Claude Code writes pipeline code for the feasibility spike. The spec (Regulatory\_Evidence\_Mapper\_SiLab\_Spec.md, dated 24 Nov 2026) remains the baseline. Nothing here redefines claim or recommendation semantics or the evidence-status taxonomy (spec §10); where a decision amends the spec, the affected section is named.

Each entry has an ID, the options considered, a recommendation and a status:

- **Decided**: confirmed by the project lead.
- **Recommended**: Claude's proposal, awaiting confirmation.
- **Open**: needs information or discussion before a recommendation is possible.
- **Blocked**: waiting on an external dependency.

Claude Code should treat only Decided entries as binding. Recommended entries become binding once the lead marks them Decided.

## Decisions already made

Four decisions are settled; the fifth is waiting on Bedrock access.

| ID | Decision | Rationale | Spec impact | Status |
| --- | --- | --- | --- | --- |
| D-01 | Inference uses open-weight models: developed on AWS Bedrock, and runnable on local hardware without code changes. | The app may need to be hosted locally if implemented. | §4.8, §7.6, §9.7: “approved Bedrock model” becomes “open-weight model available on Bedrock and locally hostable.” Embeddings follow the same rule (MI-03). | Decided |
| D-02 | Text-extractable PDF attachments are in scope for the spike sample. Scanned PDFs needing OCR stay out. | Substantive EPA comments often sit in attachments; a text-field-only sample would be skewed toward short or form comments. | §7.4.2 amended; §3.2 OCR exclusion unchanged. | Decided |
| D-03 | Target narrower EPA actions in the 300–1,000 comment range rather than major rules. | Major rules draw tens of thousands of mostly campaign comments. | §1, §7.4.1, §9.1. A DOT docket stays the backup option. | Decided |
| D-04 | Work split: Claude (chat) produces design artifacts and analyzes results; Claude Code builds the repo, acquires data and runs models. | The chat sandbox cannot reach api.regulations.gov or Bedrock. | None. | Decided |
| D-05 | Bedrock account access for development. | Access request pending. | Gates any Bedrock run; see MI-04 for interim work. | Blocked |

## Data acquisition and sampling

The biggest data risk is choosing a docket whose substantive comments turn out to be scanned, campaign-dominated or missing a response-to-comments document. DS-01 should be settled from an API query, not from memory.

| ID | Question | Options | Recommendation | Status |
| --- | --- | --- | --- | --- |
| DS-01 | Which docket criteria? | Total comment count vs. unique substantive submissions; with or without a response-to-comments (RTC) document. | Completed EPA action with a final rule and an RTC document; 300–1,000 *unique* submissions after campaign collapse; ≥80% of substantive attachments text-extractable; posted on Regulations.gov v4-era metadata. Select a primary and a backup from an API shortlist. | Open |
| DS-02 | How are campaign and near-duplicate comments handled? | (a) Exclude; (b) collapse to one representative with a member count; (c) process all. | (b): detect with shingle/MinHash similarity before extraction, process one representative, keep every member ID so the spec §4.3 invariant holds. Cluster sizes are never shown as votes. | Recommended |
| DS-03 | What is the annotation unit for long attachments? | Whole comment regardless of length; page cap; pre-selected sections. | Whole comments up to \~15 pages. For longer ones, pre-register the annotated sections before annotation and exclude unannotated text from recall denominators. | Recommended |
| DS-04 | How is PDF text extracted and located? | pdfplumber, PyMuPDF, pdftotext. | PyMuPDF for extraction; detect pages with no text layer and exclude them. Locator = document ID + page + character offset in that page's normalized text. Record extractor name and version. | Recommended |
| DS-05 | When is data fetched? | Fetch live during experiments; fetch once and freeze. | Fetch once, store raw API JSON and files with SHA-256 hashes, and never re-fetch during the spike. The manifest lists IDs, hashes, selection reasons and exclusions. | Recommended |
| DS-06 | How is the API accessed? | Personal api.data.gov key; organizational key. | Organizational key stored as a secret. Client throttles to the published limits (verify current limits in the GSA docs) and resumes from cache. | Recommended |
| DS-07 | Can attachments be stored and shown? | Internal copies only; link-out only. | Keep copies internal for analysis; demos show short excerpts with links to Regulations.gov. Some attachments are third-party copyrighted reports, so confirm with your organization. | Open |

## Annotation and measurement definitions

Several spec metrics cannot be computed until these definitions exist; AM-04 and AM-05 matter most, because without them the retrieval and conflict gates are unmeasurable.

| ID | Question | Options | Recommendation | Status |
| --- | --- | --- | --- | --- |
| AM-01 | What is one occurrence (atomicity)? | Sentence-level; proposition-level; clause-level. | One independently assessable assertion or requested action. Split conjunctions only when each part can be true/false (or adopted/rejected) on its own; qualifiers, conditions and exceptions stay attached. Worked examples go in the rubric. | Recommended |
| AM-02 | When does a predicted occurrence match a gold one? | Exact span; span overlap; semantic judgment. | Two steps: candidate match by token overlap (Jaccard ≥0.5 or containment), then one-to-one assignment, with an annotator confirming semantic equivalence on a sample. Merged and split predictions are counted as their own error types. | Recommended |
| AM-03 | How is annotator agreement measured? | Raw agreement; Cohen's κ; span F1. | Span-level F1 between annotators for extraction; Cohen's κ for pair labels. If pair κ < 0.6 on the pilot, revise the rubric before scaling up. | Recommended |
| AM-04 | How is the gold set of related pairs built for Recall@K? | Exhaustive labeling (infeasible); pooling. | TREC-style pooling: union of top-K candidates from variants A, B and C, plus all same-issue pairs in a random sample, plus constructed hard negatives, plus pairs annotators flag while reading. Report as *pooled recall* and say so. | Recommended |
| AM-05 | What sample size makes a gate rate count? | Report any rate; require minimum denominators. | A rate counts toward the gate only with ≥30 genuine conflicts, ≥100 gold occurrences and ≥50 equivalent pairs in the holdout; otherwise it is labeled directional. Report numerator/denominator and Wilson 95% intervals. | Recommended |
| AM-06 | How is the holdout split? | Random by pair; by comment; by near-duplicate cluster. | Split by comment, keeping each near-duplicate cluster on one side, so no text leaks between prompt development and evaluation. Lock the holdout (hashes in the manifest) before any prompt work; aim for ≥50% of annotated comments in it. | Recommended |
| AM-07 | How is canonicalization scored? | Pairwise P/R; B-cubed; cluster inspection. | Pairwise precision/recall over occurrence pairs. False-merge rate = merged pairs annotated non-equivalent ÷ all merged pairs. Plus manual inspection of the 20 largest clusters. | Recommended |
| AM-08 | How is evidence attribution scored? | Status accuracy only; link-level scoring. | Link-level precision/recall on (occurrence, evidence source) pairs; accuracy on the four-way evidence status; accuracy on the explicit-vs-inferred flag. | Recommended |
| AM-09 | How are quoted spans verified? | Exact match; fuzzy match. | Exact match against frozen normalized text (Unicode NFC, collapsed whitespace, PDF de-hyphenation, all documented). Fuzzy fallback is allowed but flagged in output, never silent. | Recommended |
| AM-10 | Which annotation tool? | Spreadsheet; Label Studio; doccano; custom. | Label Studio: open source, self-hostable, supports spans and relations. Confirm it is permitted on your network. | Open |

## Taxonomy and schema reconciliation

The spike labels pairs with the six-label taxonomy in §7.5, while the app model in §4.5 has about 20 relationship types. The spike stays on the six labels; the mapping below shows how each §4.5 type is recovered later through a label plus attributes.

| ID | Question | Options | Recommendation | Status |
| --- | --- | --- | --- | --- |
| TX-01 | How do §4.5 types map to §7.5 labels? | Expand the spike taxonomy; map via attributes. | Map via a `proposition_kind` field and a `subtype` attribute (table below). The spike taxonomy stays at six labels. | Recommended |
| TX-02 | Is claim → recommendation `JUSTIFIED_BY` evaluated in the spike? | Defer; within-comment only; full cross-comment. | Within-comment only: captured at extraction time when the commenter states the premise. Cross-comment justification is deferred until after the gate. | Recommended |
| TX-03 | Which evidence relationships are evaluated in the spike? | All; status + within-comment links; status only. | Evidence status plus the within-comment `CITED_AS_SUPPORT_FOR` link. Finding-to-finding comparisons (`POTENTIALLY_INCONSISTENT_WITH`) are deferred. | Recommended |
| TX-04 | Which scope fields are fixed? | Free-form; fixed list. | Fixed list: population/facility type, timeframe, geography, unit or measurement basis, condition/exception, modality (must/can/should/will). Each field carries explicit, inferred or unknown. | Recommended |
| TX-05 | Where does the issue taxonomy come from? | RTC headings; bottom-up from data; hybrid. | Hybrid: seed from the proposed rule's preamble sections, refine on the development set, freeze before holdout evaluation, always allow `UNMAPPED`. | Recommended |
| TX-06 | What is the schema source of truth? | JSON Schema by hand; Pydantic models. | Pydantic models, exported to versioned JSON Schema. Occurrence IDs are deterministic hashes of source ID + span offsets so reruns are comparable. | Recommended |
| TX-07 | Are spike pair labels directional? | Directional; symmetric. | Symmetric for the spike. Directional types (`REFINES`, `JUSTIFIED_BY`) come after the gate. | Recommended |

### TX-01 mapping

| §4.5 type | Proposition kind | §7.5 spike label | Subtype attribute |
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

The two split rows (`QUALIFIES`, `ALTERNATIVE_TO`) are where annotators are most likely to disagree; the rubric needs paired examples for each.

## Model, hosting and infrastructure

D-01 means every model in the pipeline, including embeddings, must be open-weight and runnable outside AWS. The local hardware envelope (MI-05) is the main unknown, because it caps the model sizes worth testing.

| ID | Question | Options | Recommendation | Status |
| --- | --- | --- | --- | --- |
| MI-01 | Which open-weight models are candidates? | Bedrock's catalog of open-weight families (e.g., Llama, Mistral, Qwen, gpt-oss; availability varies by region and changes). | Shortlist 2–3 models of different sizes once access is granted; select on the development set only. Prefer permissive licenses (e.g., Apache 2.0); check custom licenses such as Llama's for government-use and redistribution terms. | Blocked |
| MI-02 | How is structured output enforced? | Native JSON/tool mode; validation + bounded retry; constrained decoding. | Validation against the Pydantic schema with bounded retry on Bedrock; constrained decoding (e.g., vLLM guided JSON) when local. Schema-validity rate is logged per runtime. | Recommended |
| MI-03 | Which embedding model? | Bedrock-hosted embeddings (some are proprietary); self-hosted open model. | Self-hosted open embedding model from the start (sentence-transformers class). It runs on CPU, avoids a proprietary dependency and works before Bedrock access arrives. | Recommended |
| MI-04 | What can run before Bedrock access? | Wait; run the same open weights locally (Ollama/vLLM); use another host. | Provider-agnostic client interface now; develop against a small open-weight model locally. Results from interim runs are development only and never count toward the gate. | Open |
| MI-05 | What hardware will a local deployment have? | CPU-only server; single GPU (24–48 GB); multi-GPU. | Needed from the lead: it bounds feasible model size and the cost-per-1,000-comments projection. | Open |
| MI-06 | Will Bedrock and local runs behave the same? | Assume parity; test parity. | Test it: same weights and precision, one parity run on a holdout slice before the gate. Quantized local models are evaluated as separate variants. | Recommended |
| MI-07 | How is run-to-run stability handled? | Single run; repeated runs. | Temperature 0, fixed seeds where supported, three repeat runs on the holdout; report cluster and pair-label agreement across runs. | Recommended |
| MI-08 | Repo and tooling baseline? | Notebooks; CLI package; DVC. | Python 3.11+ CLI package with uv, pytest and JSONL artifacts; a hashed manifest in git instead of DVC for the spike. A `CLAUDE.md` file holds the guardrails Claude Code must follow. | Recommended |

## Security, privacy and data handling

Comments are public record but still contain names, addresses and occasionally health details, and any submission can contain text written to manipulate a model. These rules apply from the first line of code.

| ID | Question | Options | Recommendation | Status |
| --- | --- | --- | --- | --- |
| SP-01 | What goes into logs? | Full prompts and outputs; IDs and hashes. | Logs hold IDs, hashes, token counts, timings and errors. Full text lives only in the frozen dataset store and output JSONL, both access-controlled. | Recommended |
| SP-02 | How is prompt injection contained? | Instructions only; structural controls. | Source text inside clearly delimited data blocks; the model has no tools in the pipeline; every output is schema-validated and every quoted span verified against source (AM-09). Include a few injected test passages in the challenge set. | Recommended |
| SP-03 | Where may comment data be sent during interim development? | Local only; third-party hosted APIs. | Local only, unless your organization approves a specific host. The data is public, but the policy question is yours to settle. | Open |
| SP-04 | How are credentials handled? | Env files; secrets manager. | api.data.gov key and AWS credentials from environment or a secrets manager, never committed. `CLAUDE.md` tells Claude Code not to read or print secret files. | Recommended |

## Manual pilot: extraction, matching and canonical claims

Before building the spike pipeline, run a small manual pilot (8–12 comments, about 2–3 days) to see whether LLMs can extract claims, match equivalent claims across comments and write faithful canonical claims. Results are directional: they shape rubric v0 and prompt v0 and never count toward the gate.

| ID | Question | Options | Recommendation | Status |
| --- | --- | --- | --- | --- |
| MP-01 | Which model(s)? | Claude in chat; a local open-weight model; both. | Both, with identical prompts. Claude shows whether the task is well defined at all; the open-weight model shows the gap to what D-01 allows. Claude's results never stand in for open-weight performance. | Recommended |
| MP-02 | Which comments? | Random; targeted. | 8–12 comments on one or two issues, chosen so matches exist: a near-duplicate pair, a qualified variant (all vs. small facilities), a claim restated in different words, an apparent but not real conflict. Take them from the backup docket, or mark them dev-only so they never enter the holdout (AM-06). | Recommended |
| MP-03 | Is there a human reference? | LLM output reviewed only; independent human extraction. | One team member extracts claims from 4–5 of the comments before seeing any LLM output, so missed claims can be found, not just wrong ones. | Recommended |
| MP-04 | How are prompts structured? | One prompt for everything; one prompt per step. | One prompt per step, mirroring the spike modules: extract → match → canonicalize. Save prompt text and JSON outputs; run every step twice to see stability. | Recommended |
| MP-05 | How is matching asked? | Cluster the full claim list at once; pairwise judgments. | Try both on the same claims. Whole-list clustering works at pilot scale but not docket scale; pairwise judgment with the six §7.5 labels is what the spike would use. Compare false merges. | Recommended |
| MP-06 | How is output scored? | Impressionistic review; error tally. | A reviewer fills the scoring sheet below; report counts with denominators, not percentages dressed as gate metrics. | Recommended |
| MP-07 | What does the pilot decide? | — | (a) Rubric changes, especially atomicity and qualifiers; (b) pairwise vs. cluster matching for variant C; (c) whether canonical claims are generated or chosen from member occurrences (spec §9.3); (d) whether the open-weight gap forces a rethink of model size (MI-05). | Recommended |

### Pilot steps

1. Pick and freeze the comments; save text with hashes.
2. Human reference extraction for 4–5 comments, done blind.
3. Extraction prompt, per comment: JSON list of verbatim span, normalized statement, kind (claim or recommendation), scope fields marked explicit, inferred or unknown.
4. Span check: confirm every verbatim span appears in the source text.
5. Matching: pool all extracted claims; group equivalents; mark qualified variants as related, not equivalent.
6. Canonicalization: for each group, write a canonical statement with scope, and note qualifiers that differ across members.
7. Repeat steps 3–6 once, then score both runs.

### Scoring sheet

| Step | Error type | Definition |
| --- | --- | --- |
| Extraction | Missed | In the human reference, absent from output |
| Extraction | Invented | Output with no supporting source text |
| Extraction | Split / merged | One assertion split in two, or two assertions merged |
| Extraction | Bad span | Verbatim span not found, or points to the wrong passage |
| Extraction | Wrong kind | Claim labeled recommendation, or the reverse |
| Matching | False merge | Grouped as equivalent but differ in scope, number, unit, timeframe or condition |
| Matching | Missed match | Equivalent occurrences left in separate groups |
| Canonical | Dropped qualifier | Canonical statement loses a condition every member states |
| Canonical | Overreach | Canonical statement asserts more than any member |
| Stability | Changed output | Run 2 differs from run 1 in claims or groups |

## Pre-development work

Most of this can proceed before Bedrock access arrives; only model selection and gate-counting runs are blocked on it. Development of the pipeline itself starts once items 1–6 are done.

**Project lead**

- [ ] 1\. Mark each Recommended entry Decided, or comment with changes.
- [ ] 2\. Answer the Open entries: DS-01 (after the shortlist), DS-07, AM-10, MI-04, MI-05, SP-03.
- [ ] 3\. Obtain an organizational api.data.gov key; chase Bedrock access and ask which open-weight models are enabled in your region.
- [ ] 4\. Confirm the second annotator and their available days.

**Claude Code**

- [ ] 5\. Repo skeleton, `CLAUDE.md` guardrails and a read-only Regulations.gov script that lists candidate EPA dockets with comment counts, attachment types and RTC availability.
- [ ] 6\. Fetch-and-freeze for the chosen docket: raw JSON, files, text extraction, hashes, manifest.

**Claude (chat)**

- [ ] 7\. Review the docket shortlist and recommend a primary and a backup.
- [ ] 8\. Annotation rubric v0 with worked examples, including the TX-01 split cases.
- [ ] 9\. Experiment design: variants A/B/C, pooling procedure, metric formulas, gate thresholds with minimum counts.

**Manual pilot (before task 10)**

- [ ] 9a. Run the manual pilot: Claude drafts prompts v0 and runs the Claude pass in chat; a team member runs the same prompts on a local open-weight model and does the blind reference extraction. Findings feed tasks 8 and 9.

**Both annotators**

- [ ] 10\. Pilot the rubric on 5 comments, measure agreement (AM-03), revise, then lock the holdout before any prompt work.

## Assumptions log

These are unverified; each has a named check, and any that fails reopens the linked decisions.

| ID | Assumption | If wrong | Check | Linked |
| --- | --- | --- | --- | --- |
| A-01 | Completed, narrower EPA actions exist with 300–1,000 unique submissions, an RTC document and mostly text-extractable attachments. | Fall back to a DOT docket or relax the RTC requirement. | Shortlist script (task 5). | DS-01, D-03 |
| A-02 | The Regulations.gov API exposes attachment download links for the chosen docket. | Manual download or a different docket. | Shortlist script (task 5). | DS-05 |
| A-03 | An open-weight model on Bedrock can reach the extraction targets in spec §6.5. | The gate likely lands on NARROW or STOP. | The spike itself. | D-01, MI-01 |
| A-04 | Bedrock and local runtimes give comparable results for the same weights. | Gate results don't transfer to local deployment. | Parity run (MI-06). | MI-06 |
| A-05 | Two team members can each give enough time for dual annotation within the spike window. | Spike stretches past 2 weeks or the holdout shrinks below AM-05 minimums. | Time the rubric pilot (task 10) and extrapolate. | AM-05, AM-06 |
| A-06 | The final rule's RTC document is a useful supplementary issue reference. | Issue coverage metric loses its outside reference. | Review during docket selection. | TX-05 |
