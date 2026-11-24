# Regulatory Evidence Mapper
## SiLab Project Brief, MVP Design, Evaluation Plan, and Initial Feasibility Experiment

**Project:** Synectics Innovation Lab (SiLab)  
**Document status:** Initial product and technical specification for analysis and implementation planning  
**Date:** November 24, 2026  
**Primary implementation assistant:** Claude (analysis and development)  
**Delivery model:** Reusable, deployable accelerator—not a fully productized SaaS offering

> **Governing principle:** Before building an application, demonstrate that a small, reproducible analytical pipeline can reliably extract claims and recommendations, preserve their sources, identify equivalent propositions, and detect meaningful relationships. The user-facing graph must not lend false credibility to unreliable AI inferences.

---

# 1. Executive summary

The **Regulatory Evidence Mapper** is an AI-assisted accelerator for organizing and analyzing public comments on proposed government regulations and other public initiatives. It ingests public docket materials, extracts individual factual/assertive **claims** and normative/policy **recommendations**, groups semantically equivalent occurrences into canonical propositions, links claims and recommendations to evidence actually provided or referenced in the submission, and proposes typed relationships such as contradiction, qualification, justification, and conflicting recommendations.

Its primary output is a **source-linked issue matrix** for reviewing what commenters asserted, what they requested, what supporting material they supplied, and where propositions or recommended actions agree, diverge, or appear inconsistent. A **contextual argument-graph drill-down** helps users explore a selected claim, recommendation, issue, or evidence finding without presenting a visually overwhelming docket-wide graph.

The initial demonstration will use **one completed EPA or DOT federal rulemaking docket**, ideally containing approximately **300–1,000 public comments**, with the proposed rule and the agency's final rule and/or response-to-comments document available. Ingestion will use the publicly accessible Regulations.gov API where practical. The underlying accelerator should be adaptable to state/local consultation workflows (e.g., zoning changes, transportation plans, parks) through new source adapters and configuration, but those are **not** MVP integrations.

The solution **does not** decide whether a comment is true, legally persuasive, scientifically valid, or worthy of adoption. “Evidence supplied” indicates that a submission contains or cites material offered in support of a specific assertion; it does **not** imply that the evidence has been independently verified. AI-produced relationships remain reviewable proposals.

**Initial implementation sequence:**

1. Conduct a small **argument-extraction and relationship-inference feasibility spike** using real comment text, with a manually curated evaluation set produced by project team members (not agency analysts).
2. Decide whether the analytical engine is feasible, needs narrowing, or should be stopped.
3. Only after the gate, develop ingestion, persistence, issue-matrix UI, localized graph drill-down, and export.

**Tentative total prototype timeframe:** 6–8 weeks, conditional on feasibility and staffing. The feasibility spike is approximately 1–2 weeks. These are planning assumptions, not delivery guarantees.

---

# 2. Problem, intended users, and value proposition

## 2.1 Problem

Public comments on proposed rules range from short expressions of preference to long submissions containing multiple technical arguments, calculations, legal concerns, alternative proposals, references, and attachments. A single comment can address several different regulatory provisions. Across hundreds of comments, essentially the same proposition may be stated in different words, while superficially conflicting assertions may refer to different populations, time periods, assumptions, or measurement bases.

Ordinary topic modeling and summarization help sort text but do not adequately preserve **atomic propositions**, their **precise source passages**, the **evidence offered for each**, or the **logical and policy relationships** between propositions.

## 2.2 Intended users and use cases

- **Federal regulatory review teams:** EPA, DOT, and potentially other agencies reviewing a docket.
- **Regulatory analysts, program staff, and technical specialists:** users who need structured issue summaries and traceable comment relationships.
- **Government contractors performing comment review support:** potential implementers and operational users.
- **Future nonfederal users:** state and local government teams reviewing comments on zoning, parks, transportation, or other public proposals.

The prototype is developed **on spec without access to agency analysts**. Thus, suitability for the actual agency workflow is an explicit **unvalidated assumption**, and no claim of measured analyst time savings will be made.

## 2.3 Differentiation

The accelerator focuses on **claim- and recommendation-level argument analysis**, not simply comment retrieval, topic classification, sentiment analysis, or document summaries. Differentiating capabilities are:

- Separate factual/assertive claims from normative/policy recommendations.
- Preserve occurrences in original documents while canonicalizing equivalent propositions across submissions.
- Identify the difference between factual contradictions and incompatible proposed policy actions.
- Handle complete, partial, apparent, and conditional conflicts without forcing binary classifications.
- Attribute evidence to the specific assertion or recommendation for which it was supplied.
- Provide inspectable, source-linked explanations of AI-proposed graph edges.

---

# 3. MVP feature list and scope

## 3.1 In scope, after the feasibility gate

| ID | Feature | MVP behavior / acceptance intent |
|---|---|---|
| F1 | Docket ingestion | Import one chosen completed docket's public metadata, proposed-rule document(s), comments, and supported attachments; retain external identifiers and ingestion status. |
| F2 | Text preparation and provenance | Parse comment text and text-extractable PDFs; retain source documents and locatable passages (character offsets for text; page/section when available). |
| F3 | Atomic extraction | Extract **claim occurrences** and **recommendation occurrences**, including qualifiers, relevant issue/provision candidates, original quoted span, and extraction metadata. |
| F4 | Canonicalization | Cluster/associate occurrences that express substantively equivalent claims or recommendations; avoid merging materially different scopes. |
| F5 | Evidence mapping | Record evidence sources and specific findings when identifiable; distinguish evidence **included**, external evidence **cited but not fetched**, **no evidence identified**, and **unclear**. |
| F6 | Typed relationship inference | Propose relationships among claims, recommendations, and evidence, preserving scope, rationale, source references, model/run provenance, uncertainty, and review status. |
| F7 | Issue/provision mapping | Group content by a bounded issue taxonomy and, where feasible, proposed-rule provisions; allow unknown/unmapped values. |
| F8 | Source-linked issue matrix | Search/filter by issue, provision, claims, recommendations, evidence status, and proposed conflicts; inspect and export structured findings to CSV/XLSX. |
| F9 | Contextual graph drill-down | From a selected claim or recommendation, show a small first-degree neighborhood with typed edges, filters, selective expansion, and a detail/source panel. |
| F10 | Evaluation and operational telemetry | Capture stage-level quality metrics on labeled samples, processing failures, throughput, cost, versions, and repeat-run stability. |

**Review handling for MVP:** AI-inferred propositions and relationships are labeled **proposed / unreviewed**, not certified facts. A light review control (e.g., accepted/rejected/needs-review and corrected text) is desirable if time permits, but the demonstration must not imply agency validation.

## 3.2 Explicitly out of scope

- Fully automated legal analysis, scientific fact-checking, claim truth or credibility scoring, or final agency response drafting.
- Automated acceptance/rejection of public comments or regulatory decisions.
- OCR of complex scanned attachments, sophisticated table reconstruction, or multimedia transcription.
- Live monitoring of dockets, continuous ingestion, or automatic comment submission.
- Broad production integrations with internal agency systems or authentication/authorization accreditation.
- Processing every conceivable regulatory document format, jurisdiction, or domain.
- A full-docket force-directed network as the primary UI.
- Comprehensive formal logic or theorem proving.
- Reliable causal interpretation of evidence or research methodology evaluation.

## 3.3 Delivery artifacts

1. Reproducible Python ingestion and analytical processing modules.
2. Documented schema, relationship taxonomy, and source provenance model.
3. A small relational datastore and application/API (subject to feasibility).
4. Source-linked issue matrix, contextual graph drill-down, and structured export.
5. Evaluation dataset, annotation rubric, automated metrics, experiment results, error analysis, and model/run configuration.
6. Deployment instructions for an AWS-compatible demonstration environment.

---

# 4. Design decisions and logical data model

## 4.1 Model two interconnected layers

**Documentary/provenance layer** represents verifiable public-record structure. **Argumentation layer** represents AI-extracted propositions and inferred relationships. These must not be confused.

Simplified documentary flow:

```text
Docket
  ├─ Documents (proposed rule, final rule, supporting material)
  └─ Comments responding to specific document(s)
       ├─ Comment text and attachments
       ├─ Claim occurrences
       └─ Recommendation occurrences
```

Argumentation relationships connect occurrences to canonical entities, issues, provisions, evidence, and one another:

```text
ClaimOccurrence ──EXPRESSES──> CanonicalClaim ──ADDRESSES──> Issue/Provision
RecommendationOccurrence ──EXPRESSES──> CanonicalRecommendation
CanonicalRecommendation ──JUSTIFIED_BY──> CanonicalClaim
EvidenceFinding ──CITED_AS_SUPPORT_FOR / CHALLENGES──> Claim or Recommendation
CanonicalClaim <──CONTRADICTS / QUALIFIES / RELATED_TO──> CanonicalClaim
CanonicalRecommendation <──CONFLICTS_WITH / ALTERNATIVE_TO──> CanonicalRecommendation
EvidenceFinding <──DISAGREES_WITH / QUALIFIES──> EvidenceFinding
```

**Important data modeling refinement:** While a docket contains multiple documents and a comment commonly responds to a particular proposed-rule document, the public record should **not** be forced into a strict tree. Preserve external docket/document/comment identifiers and actual API links. Attachments are sources associated with comments; some source documents may be reused or cited across occurrences.

## 4.2 Entity catalog

| Entity | Meaning | Key attributes (illustrative) |
|---|---|---|
| `Docket` | Regulatory proceeding | external docket ID, agency, title, status |
| `Document` | Proposed rule, final rule, notice, study, or attachment | external document ID, type, parent/link, URL, file metadata |
| `Comment` | Individual submitted public comment | external comment ID, comment-on document ID, posted date, text, URL |
| `Issue` | Regulatory topic under analysis | issue ID, label, description, parent issue (optional) |
| `RegulatoryProvision` | Section/requirement from a proposed rule | section identifier, text, source document |
| `ClaimOccurrence` | A specific factual/assertive statement in a specific comment/source | occurrence ID, verbatim span, normalized text, qualifiers, source locator |
| `CanonicalClaim` | Normalized proposition potentially expressed in many occurrences | canonical ID, normalized proposition, scope/context fields |
| `RecommendationOccurrence` | A specific requested agency action in a comment | occurrence ID, verbatim span, extracted action/target/scope |
| `CanonicalRecommendation` | Normalized policy action potentially requested by many comments | canonical ID, action, target, affected population, condition/deadline |
| `EvidenceSource` | Submitted/cited document, dataset, calculation, study, or firsthand account | source ID, source type, included vs cited-only, location/reference |
| `EvidenceFinding` | A specific relevant finding/measurement/assertion inside an evidence source | finding ID, description, numerical/context fields, exact locator |
| `Relationship` | Typed directed or symmetric link between compatible entities | endpoints, type, scope overlap, rationale, model/run, status |
| `ProcessingRun` | Reproducibility/audit record for an extraction or inference batch | model, prompt/version, timestamp, parameters, dataset version, cost |

## 4.3 Cardinality and identity rules

- Docket → Documents: typically **one-to-many**. A docket can include many kinds of documents.
- Docket/Document → Comments: a comment belongs to a docket and can refer to a particular rulemaking document; preserve actual source identifiers rather than assume a universal one-to-many tree.
- Comment → ClaimOccurrences / RecommendationOccurrences: **one-to-many**, potentially zero occurrences for non-substantive comments.
- Occurrence → Canonical proposition: **many-to-one when confidently mapped**, with unresolved occurrences allowed. Canonical propositions correspond to meaning, not commenter identity.
- CanonicalClaim ↔ Issue / Provision: **many-to-many**.
- CanonicalRecommendation ↔ Issue / Provision: **many-to-many**.
- Claims/recommendations ↔ EvidenceFindings: **many-to-many**. A cited finding can be used toward multiple conclusions or interpreted differently by commenters.
- EvidenceSource → EvidenceFindings: **one-to-many** when findings are extracted; a source may simply be cited without its content being available.
- Claims ↔ Claims, Recommendations ↔ Recommendations, EvidenceFindings ↔ EvidenceFindings: **many-to-many** typed comparisons.

**Critical invariant:** Never discard occurrences when producing canonical entities. The counts, provenance, qualifying text, and evidence usage of each specific comment must remain recoverable. Also avoid treating the number of occurrences as votes or evidence of truth; near-duplicate or campaign comments may require separate handling.

## 4.4 Claims versus recommendations

- A **claim** asserts, predicts, assumes, or describes something about the world (e.g., “equipment installation takes at least 36 months”).
- A **recommendation** urges a policy action (e.g., “extend the compliance deadline to 36 months”).
- A recommendation can be `JUSTIFIED_BY` one or more claims and can cite the same evidence as another recommendation.
- Two recommendations may `CONFLICT_WITH` even when they share the **same claim and evidence**. This is a policy disagreement, not a factual contradiction.
- A claim may be used as a stated premise of a recommendation without logically entailing the requested action. Store the **attributed rationale** and distinguish the commenter's stated reasoning from AI-inferred assumptions.

## 4.5 Relationships and their semantics

Recommended initial relationship families (not all need separate database tables):

| Family | Types | Semantics / caution |
|---|---|---|
| Documentary | `CONTAINS`, `RESPONDS_TO`, `APPEARS_IN`, `CITES`, `EXPRESSES` | Derived from source records and explicit extraction positions, with provenance |
| Context | `ADDRESSES_ISSUE`, `CONCERNS_PROVISION` | Proposed mapping to topic/regulatory section |
| Claims | `EQUIVALENT_TO`, `CONTRADICTS`, `QUALIFIES`, `RELATED_TO` | Truth-conditional relation must account for overlap in population, period, units, conditions, and modality |
| Recommendations | `EQUIVALENT_TO`, `CONFLICTS_WITH`, `PARTIALLY_CONFLICTS_WITH`, `ALTERNATIVE_TO`, `REFINES` | Incompatible proposed actions are not automatically contradictory factual assertions |
| Argument/evidence | `JUSTIFIED_BY`, `CITED_AS_SUPPORT_FOR`, `CITED_TO_CHALLENGE`, `CHALLENGES` | Attribute **how the source uses evidence**; do not assert scientific validity |
| Evidence comparisons | `POTENTIALLY_INCONSISTENT_WITH`, `QUALIFIES` | Compare findings only after checking methods, populations, periods, and measurement bases |

To avoid an explosion of relationship types, store **scope and conflict degree as attributes** (e.g., `complete`, `partial`, `apparent`, `undetermined`) when appropriate. The initial spike should use a **small classification taxonomy** and expand only after evidence of reliable model performance.

### Partial or apparent conflict example

- A: “All facilities need 36 months.”
- B: “All facilities can comply in 24 months.”
- C: “Small facilities can comply in 24 months, but large facilities need 36 months.”

A and B potentially contradict if they address the same meaning of “need/can comply” and conditions. C **qualifies** the broader propositions and can create a **partial conflict** over the large-facility population, not a global contradiction. The engine should identify the dimension of disagreement and be permitted to abstain.

## 4.6 Evidence status and truthfulness boundary

The evidence-status taxonomy describes **what the submission provides**, not whether the claim is true:

1. `EVIDENCE_INCLUDED` — potentially relevant data, calculation, passage, attachment, or firsthand information provided in the processed submission.
2. `EXTERNAL_EVIDENCE_CITED` — an external source is referenced but not verified/retrieved.
3. `NO_EVIDENCE_IDENTIFIED` — none found in the processed materials (not proof none exists).
4. `EVIDENCE_UNCLEAR` — relationship between cited material and the claim needs inspection.

Record whether the commenter **explicitly** connects evidence to a claim/recommendation or whether an association was **AI-inferred**. A submission can raise an important legal, normative, experiential, or policy concern without formal evidence. Never imply `NO_EVIDENCE_IDENTIFIED` means “false,” “invalid,” or “unimportant.”

## 4.7 Structured representation, provenance, and uncertainty

For propositions and recommendation actions, extract structured context **when explicitly stated or confidently supported by text**:

- subject / action / target / predicate;
- numerical value, unit, comparison operator (when applicable);
- affected population or facility type;
- timeframe, date, regulatory provision;
- stated assumptions, exceptions, conditions;
- whether details are explicit, inferred, or unknown.

Every AI-created occurrence or inferred relationship should retain:

- original source IDs and quoted text span(s);
- precise file locator if possible (offsets, page, section, table);
- model and prompt/version IDs, processing run ID;
- short explanation and scope/comparison attributes;
- confidence or uncertainty as an **engineering diagnostic**, not as probability of claim truth;
- review status (`PROPOSED`, `ACCEPTED`, `REJECTED`, `NEEDS_REVIEW`) where human review is supported.

Missing or ambiguous information should stay missing/ambiguous; do not invent values to complete the graph. Treat source content as untrusted text, including potential prompt injection in public submissions.

## 4.8 Storage and system architecture

**Provisional MVP choice:** PostgreSQL (plus optional pgvector for embeddings), not a dedicated graph database. Use relational entity tables and typed link tables to represent the graph. The graph is a conceptual model; Neo4j is not required to demonstrate it.

**AWS-oriented stack:** Python processing jobs; S3 for originals and extracted text; PostgreSQL; AWS Bedrock for structured extraction and relation classification; FastAPI for query endpoints; Streamlit as the main review interface, potentially embedding Cytoscape.js for graph drill-down. Use known/reviewed configurations, restrict credentials, and log operational events without unnecessarily retaining sensitive content.

**Candidate relationship pipeline:**

```text
Source records + document text
  -> atomic claims and recommendations + source spans
  -> normalization / candidate canonical grouping
  -> issue/provision matching
  -> high-recall retrieval of potentially related propositions
  -> contextual relation classification (with abstention)
  -> graph edges with explicit provenance and review state
  -> issue matrix, exports, contextual visualization
```

Do **not** compare every proposition against every other proposition with an LLM. Pair counts grow as `n(n-1)/2`. Candidate retrieval and filtering are required to control cost—but retrieval recall must be evaluated so that true conflicts are not systematically discarded.

---

# 5. UI / UX decisions

## 5.1 Primary workflow: issue matrix, not a giant graph

The primary screen is an **issue-oriented analyst workspace**:

- Choose a docket and regulatory issue/provision.
- See related canonical claims, canonical recommendations, evidence status, and candidate conflicts.
- Drill into an item to see exact occurrences, source text, related entities, and reasoned relationship proposals.
- Export a source-linked issue/evidence matrix.

Do not force users to navigate a full docket-level network. A network containing hundreds of nodes would be difficult to interpret and could conceal model errors.

## 5.2 Contextual graph drill-down

The graph is an **optional, meaningful exploratory view** launched from a selected claim or recommendation. Initial neighborhood: approximately **5–20 nodes**, first-degree neighbors, with selective expansion. Suggested views:

- **Claim-centric:** supporting/challenging evidence, related and conflicting claims, recommendations relying on the claim.
- **Recommendation-centric:** justifying claims, cited evidence, competing or partially conflicting recommendations.
- **Issue-centric:** possible stretch feature; aggregate only the issue's principal propositions and relationship clusters.

Interactions:

1. Select a node to inspect its statement, source occurrences, supporting passages, and review state.
2. Filter by node/relationship type and AI proposal versus verified source link.
3. Expand a node's immediate neighborhood on demand.
4. Compare two selected claims/recommendations, highlighting common evidence and conditional differences.
5. Open original comment/attachment at the relevant passage.

**Presentation semantics:** Use visual styles and a legend for node types and edge types. Distinguish directional support/justification from symmetric conflict; show uncertain/inferred edges differently from verified source links. Never imply that an attractive graph proves a relationship.

**MVP priority:** claim/recommendation neighborhood, edge filtering, selected-node details, provenance navigation. Full path highlighting and sophisticated side-by-side comparison may follow if time allows.

---

# 6. Business, product, and technical metrics

## 6.1 Measurement principles

This is an **on-spec prototype without agency analysts**. Accordingly:

- **DO NOT use analyst time reduction as an MVP success metric.** There is no credible baseline or representative reviewer population to measure it.
- Do not assert validated operational efficiency or agency acceptance.
- Use measurable proxies: substantive-issue coverage against a reference set, completeness of the issue matrix, quality of evidence and provenance mapping, and the cost/throughput of processing.
- Human annotations for the experiment may be produced by project team members. Label these as **team-created reference annotations**, not regulator-validated ground truth.
- Report both stage-specific and **end-to-end** performance; success at one intermediate stage may conceal errors elsewhere.

## 6.2 Product/business-facing proxy metrics

| Metric | Definition | Data source / measurement | Goal |
|---|---|---|---|
| Substantive issue coverage | Fraction of manually identified substantive issues found in the resulting issue matrix | Team-adjudicated issue reference set; completed docket's final rule/response-to-comments as supplementary context | High recall; benchmark during experiment |
| Issue matrix completeness | Fraction of required fields correctly populated for sampled items (issue, claim/recommendation, source, evidence status, relationship where applicable) | Manually scored exported records | Improve by iteration; set acceptance gate |
| Traceable finding coverage | Fraction of displayed extracted statements/edges with recoverable original source references | Automated locator checks + manual verification sample | Target near 100% structurally; correctness assessed separately |
| Reviewer correction burden (proxy) | Number and severity of corrections needed to turn AI output into a credible matrix | Team review of sample; categorize omission, false merge, false conflict, wrong evidence | Lower is better; report per 100 items |
| Portability / reuse | Effort to load a second docket without changing core inference logic | Configuration-only or adapter-only second-docket smoke test, if feasible | No bespoke core redesign |

**Do not claim that final-rule issue headings are a complete gold standard**. They reflect agency decisions and editorial organization; use them to assess practical relevance, not as the sole source of labels.

## 6.3 Core AI quality metrics

| Stage | Metric | How measured | Why it matters |
|---|---|---|---|
| Claim extraction | Precision, recall, F1 at occurrence level | Human source-span annotations | Prevent omissions and invented atomic claims |
| Recommendation extraction | Precision, recall, F1 at occurrence level | Human annotations of requested actions | Preserve actual policy requests |
| Canonicalization | Pairwise precision/recall/F1; false-merge rate; cluster inspection | Adjudicated equivalent/non-equivalent occurrence pairs | False merges may erase critical qualifiers |
| Candidate retrieval | Recall@K / fraction of labeled related/conflicting pairs retrieved | Gold related pairs before classifier | A missed candidate can never be classified |
| Relationship classification | Precision, recall, F1 **by type** and confusion matrix | Adjudicated candidate pairs | Distinguish contradictions, qualifications, recommendations, and no-conflict |
| Scope understanding | Agreement on population, timeframe, conditions, qualifiers | Annotated claims and pairs | Partial-conflict reasoning depends on scope |
| Evidence mapping | Link precision and coverage; evidence-status accuracy | Manual passage/finding review | Prevent false attribution of evidence |
| Source provenance | Citation/locator correctness | Manually open sampled spans and documents | Core requirement for inspectability |
| Abstention calibration | Accuracy at confidence/coverage thresholds and unresolved proportion | Human-labeled ambiguous cases | Avoid forced classifications in unclear situations |
| End-to-end issue/relationship recall | Fraction of true issue/relationship targets surfaced from raw comments through all stages | Gold reference, starting from original text | Captures compounding pipeline failures |

For relationship classification, distinguish **conditional performance** (given the right extracted and retrieved pair) from **end-to-end performance** (starting with raw comments).

## 6.4 Engineering and operations metrics

| Metric | Definition |
|---|---|
| Ingestion completeness | Retrieved eligible public records / expected public records for selected docket, accounting for API limits/availability |
| Parsing success | Parseable supported files / attempted supported files; separately track unsupported/corrupt files |
| Schema validation | Valid structured model outputs after bounded retry / total attempted outputs |
| Stage completion and error rate | Successful items by ingestion, parsing, extraction, clustering, retrieval, relation, graph persistence |
| Latency and throughput | Wall-clock by stage, comments/minute, total time for sample docket |
| API / compute cost | Bedrock token use and cost, plus infrastructure estimate; report **cost per 1,000 comments** |
| Stability/reproducibility | Consistency across repeated runs on frozen inputs and model/prompt versions (pairwise relationship and cluster agreement) |
| Candidate efficiency | Number of retrieved pairs and LLM pairs evaluated vs all theoretical pairs; recall retained |
| Graph integrity | Broken references, orphan nodes, invalid edge endpoints, missing source IDs, schema violations |
| Version traceability | Percentage of outputs with dataset, model, prompt, and processing-run identifiers |

## 6.5 Suggested feasibility gates (provisional targets)

These are **targets for evaluation design**, not externally validated benchmarks or performance claims:

| Metric | Proposed target |
|---|---:|
| Claim/recommendation occurrence extraction recall | ≥ 90% |
| Occurrence extraction precision | ≥ 90% |
| Canonical equivalence precision | ≥ 95% |
| Relevant candidate relationship retrieval recall | ≥ 95% |
| Proposed direct-conflict classification precision | ≥ 90% |
| Source attribution correctness | ≥ 98% |
| Structured output validity after bounded retries | ≥ 99% |

**Interpretation requirements:** An initial 25–30-comment annotated subset is too small to substantiate these rates with narrow confidence intervals, particularly for rare contradictions. Record numerators/denominators, uncertainty intervals when useful, label balance, and the count of genuine conflicts. Treat these as directional go/no-go criteria until a larger blind holdout set is available. A system that abstains on ambiguous relationships may be preferable to one making confident, incorrect claims. Set a minimum coverage floor when assessing high precision.

---

# 7. Highest-risk assumptions and first experiment

## 7.1 Primary technical risk

The hardest and highest-risk part is **semantic normalization and typed relationship inference**: accurately distinguishing equivalent propositions from qualified variants, direct from partial/apparent contradictions, and conflicting recommendations from factual disagreements. Upstream extraction and attribution errors can propagate into credible-looking but incorrect graph relationships.

Other important risks are source-span attribution, attachment parsing, retrieval recall, model consistency, and data heterogeneity. These are secondary to proving reliable core argument analysis in the first spike.

## 7.2 Primary business/product risk

Even if relationships are technically accurate, they may not help actual regulatory teams. Without agency analysts, this remains **unvalidated**. The prototype can establish technical feasibility and evidence traceability, not claim proven workflow adoption or staff time savings.

## 7.3 Experiment objective and decision question

**Name:** Argument Relationship Feasibility Spike  
**Timebox:** Approximately 1–2 weeks  
**Resources:** One AI engineer implementing, a second team member or project lead independently labeling/reviewing a subset. No agency analyst participation required.  
**Decision:** Is the analytical core accurate, sufficiently traceable, and economically plausible to justify building the full application?

### Hypotheses to test

- **H1:** An LLM can extract substantive claim and recommendation occurrences from text with sufficient recall and accurate source attribution.
- **H2:** Canonicalization can group equivalent occurrences while preserving meaningful conditions, scope, and exceptions.
- **H3:** A retrieval + LLM classification pipeline can detect candidate argumentative relationships with high recall and acceptable precision, distinguishing factual contradictions from policy conflicts.
- **H4:** These results are stable enough across repeated runs and affordable enough for a 300–1,000-comment docket.

## 7.4 Data selection

1. Choose **one completed EPA or DOT docket** with a final rule and ideally a response-to-comments document.
2. Select **60–80 publicly available comments** with readily accessible text (no complex OCR). Include:
   - short and long comments;
   - comments raising multiple claims and recommendations;
   - apparent near-duplicates;
   - arguments with critical exceptions or scope conditions;
   - cited studies or calculations;
   - competing factual assertions and policy recommendations.
3. Use stratified/targeted sampling for challenge cases; record selection criteria and avoid representing the sample as random or fully representative.
4. Keep original IDs and source text frozen; record a dataset manifest and content hashes.
5. Optionally use the agency's final response-to-comments as a **supplementary issue taxonomy reference**, not as a perfect label set.

## 7.5 Manual reference annotation (by project team)

Two team members independently annotate an initial **25–30 comments**, resolve disagreements, and document a concise rubric. Expand the adjudicated set if feasible; maintain a **held-out subset** not used to develop prompts or thresholds.

Annotate:

- claim occurrence text/span and proposition;
- recommendation occurrence text/span, proposed action, target and scope;
- issue/provision when discernible;
- evidence citation/inclusion and exact reference where accessible;
- equivalence/non-equivalence across candidate occurrences;
- selected cross-proposition relationships, including negative/unrelated pairs;
- explicit versus inferred qualifiers and assumptions.

**Initial pair-label taxonomy:** `EQUIVALENT`, `DIRECT_CONFLICT`, `PARTIAL_OR_QUALIFIED_CONFLICT`, `RELATED_COMPATIBLE`, `UNRELATED`, `INDETERMINATE`. For recommendations, interpret conflict as incompatibility of actions; maintain a separate proposition-kind field. A small taxonomy is preferable to a complex one until the model is tested.

Important annotation practices:

- Define atomicity rules (one independently assessable assertion or policy request per occurrence).
- Include **hard negatives**: superficially similar pairs that differ by population, method, unit, timeframe, or conditions.
- Separate explicit text from annotator interpretation.
- Measure annotator agreement, record ambiguous labels, and adjudicate rather than forcing agreement silently.
- Do not use the same adjudicated examples for prompt tuning and final evaluation.

## 7.6 Minimal experimental pipeline (no full application)

```text
Frozen comment text
    ↓
1. Structured extraction (claims, recommendations, exact source spans)
    ↓
2. Candidate normalization / canonical equivalence grouping
    ↓
3. Related-pair candidate generation (issue filters + embeddings, high recall)
    ↓
4. Pair classification (equivalent/conflict/qualified/compatible/unrelated/unknown)
    ↓
5. Evidence and rationale attribution checks
    ↓
6. Offline evaluation, error analysis, and cost/stability report
```

**Implementation:** Python notebooks/scripts or CLI; versioned JSONL input/output; Pydantic/JSON Schema for outputs; embeddings and AWS Bedrock for model calls, or a clearly documented approved test model. No database, UI, graph visualization, or production API required for the spike.

Log model ID, parameters, prompt version, timestamps, retries, token usage/cost, source ID, and extraction/classification outputs. In responses, require source spans; verify copied spans exist in the cited source text and inspect semantic attribution manually.

## 7.7 Experimental comparisons and ablations

Test at least three variants using the **same held-out labels**:

| Variant | Description | Purpose |
|---|---|---|
| A — Basic baseline | Embedding similarity, thresholds, simple text/rule heuristics | Establish inexpensive lower-complexity reference |
| B — LLM direct | LLM extraction + direct pair assessment on a **bounded labeled set**, not every docket pair | Establish model-only baseline |
| C — Hybrid | Extract structured occurrences → retrieve candidates → LLM classify → optional deterministic validation | Test proposed architecture |

Additionally compare retrieval using embeddings alone vs issue-filtered embeddings, and assess whether scope fields improve false-conflict rates. Keep prompts/models fixed within each comparison and record evaluation-set contamination/prompt-tuning decisions.

## 7.8 Adversarial/challenge cases

Construct **20–30 explicitly labeled difficult pairs**, separate from the main naturalistic sample where feasible:

- All facilities versus small/large facilities only.
- Estimated future cost versus historical observed cost.
- Same numerical value in different units, dollars, years, or denominators.
- Same evidence invoked to justify two incompatible deadlines.
- Same recommendation based on different premises.
- A broad claim with an exception or conditional qualifier.
- Inconsistent scientific findings based on different study methods.
- A cited external document not actually provided.
- Two policy options that differ but can be jointly adopted.

Synthetic cases may be used for stress tests but **must be reported separately** from real-comment performance. Ensure the test has genuine positive conflicts; otherwise conflict precision/recall is uninterpretable.

## 7.9 Evaluation outputs

The spike should produce:

1. **Frozen dataset manifest** with public docket IDs, selection criteria, and excluded formats.
2. **Annotation guidelines**, raw reviewer annotations, adjudicated labels, and a holdout policy.
3. **Pipeline code**, versioned prompts/configuration, JSONL outputs, run metadata, and cost logs.
4. **Quality scorecard** with denominators, per-stage metrics, candidate retrieval recall, and end-to-end results.
5. **Error taxonomy** with representative failures: missed extraction, over-splitting, false canonical merge, wrong qualifier, wrong evidence, omitted relevant pair, false conflict, abstention.
6. **Stability/cost analysis** across repeated runs and a reasoned projection to 300–1,000 comments (clearly distinguished from measured full-docket cost).
7. **Go / narrow / stop recommendation** with the evidence supporting it.

## 7.10 Gate decisions

**GO — Build graph-based MVP** if extraction, canonicalization, evidence attribution, and relationship inference are accurate enough on adjudicated examples and have a credible path to scaled cost and throughput. Proceed with one docket ingestion and UI.

**NARROW — Issue/recommendation mapper** if extraction, canonical grouping, and source linking work but contradiction detection remains too noisy. Show candidate related claims/recommendations and avoid definitive conflict edges. This is a valid and potentially useful reduced product.

**STOP / REFRAME** if source attribution or canonical grouping cannot be made reliable at acceptable cost. A persuasive-looking argument graph with incorrect connections is not an acceptable deliverable.

Do not automatically advance solely because top-line F1 clears a threshold. Review false merges, missed significant issues, incorrectly attributed evidence, and failure cases that could materially mislead users.

---

# 8. Conditional 6–8-week delivery sequence

| Period | Goal | Exit criteria / output |
|---|---|---|
| Weeks 1–2 | Argument Relationship Feasibility Spike | Measured results and formal go/narrow/stop decision |
| Week 3 | Docket ingestion and source/provenance persistence | One selected docket ingested with traceable IDs and supported text |
| Weeks 4–5 | Canonical entities, relationships, evidence mapping, and export | Versioned end-to-end analytical pipeline, stage metrics |
| Week 6 | Source-linked issue matrix and contextual graph | Drill down to occurrence passages and localized relation neighborhoods |
| Weeks 7–8 | Quality assessment, second-docket smoke test if feasible, demo and documentation | Scorecard, known limitations, reproducible deployment/demo |

This schedule presumes the feasibility spike succeeds and the MVP remains limited to text and extractable PDFs. It does not include federal production authorization or integrations with nonpublic agency systems.

---

# 9. Open decisions for Claude-led analysis

These are **questions to resolve with explicit alternatives and tradeoffs**, not permission to expand MVP scope without review:

1. **Docket selection:** Which two or three completed EPA/DOT dockets meet the target volume, manageable attachment profile, and availability of final response-to-comments material? Select one for the spike and one candidate backup.
2. **Atomicity:** What annotation rubric yields acceptable inter-annotator agreement on claims versus compound claims, recommendations, and qualifiers?
3. **Canonicalization:** Should the first implementation use exact/semantic pair matching plus cautious cluster creation, or propose canonical entities directly? Evaluate false-merge risk.
4. **Relationship representation:** Which minimum labels and scope attributes are both useful and reliably detectable? Favor fewer well-defined labels.
5. **Retrieval:** What K and candidate-generation strategy delivers near-complete recall of annotated meaningful pairs at a practical cost?
6. **Evidence granularity:** When should a cited report remain a source-only reference, and when should the engine extract a distinct finding?
7. **Model/prompt evaluation:** What approved Bedrock model/configuration and prompt structure perform best on the held-out tests without excessive cost?
8. **UI stack:** Can embedded Cytoscape.js inside Streamlit support node and edge inspection reliably, or would a small React app be simpler for the interactive drill-down?
9. **Portability:** Which configuration and adapter contracts let a second docket—and later state/local records—use the same core argument engine?

---

# 10. Working instructions for Claude

Use this specification as the **initial project baseline**. First perform a **read-only design and feasibility review**: identify ambiguities, invalid assumptions, security/provenance risks, and missing measurement definitions. Propose concrete adjustments in a short decision register. Do not silently redefine claim/recommendation semantics, change the evidence-status taxonomy, or add broad autonomous features.

Then implement the **feasibility spike first**, not the full application. Before writing complex components, produce:

- the proposed annotation rubric and schema;
- dataset selection criteria and acquisition plan;
- baseline and hybrid experiment designs;
- run logging and evaluation methodology;
- explicit gate criteria and limitations.

Keep extraction, canonicalization, candidate retrieval, classification, and evaluation as separate modules so failures can be localized. Favor reproducibility, provenance, small interfaces, and testable functions over broad feature coverage. Do not treat generated relationships as verified facts. All conclusions about quality must be supported by measured outputs; mark assumptions as assumptions.

---

# 11. Useful authoritative reference starting points

- **Regulations.gov API (GSA):** https://open.gsa.gov/api/regulationsgov/
- **Regulations.gov public portal:** https://www.regulations.gov/
- **Federal Register:** https://www.federalregister.gov/
- **DOT rulemaking process:** https://www.transportation.gov/regulations/rulemaking-process
- **GAO report on public-comment management (GAO-20-383R):** https://www.gao.gov/products/gao-20-383r
- **EPA Action Development Process guidance (historical):** https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=940066AZ.txt
- **Administrative Conference of the United States (ACUS), public-comment processing project:** https://www.acus.gov/projects/processing-public-comments-agency-rulemaking

These references are starting points for implementation and validation, not evidence that the proposed accelerator has already delivered claimed benefits.
