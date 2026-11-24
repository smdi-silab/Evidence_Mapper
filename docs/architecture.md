# Architecture

> Keep this document current. Update it whenever a spec changes the shape of the system.

## Overview
Regulatory Evidence Mapper turns the public comments on a regulatory docket into source-linked claims, recommendations, evidence links, and proposed relationships. See the SiLab spec ([`specs/Regulatory_Evidence_Mapper_SiLab_Spec.md`](../specs/Regulatory_Evidence_Mapper_SiLab_Spec.md)) §1 and §4.

The project is in its **feasibility spike** ([ADR 0002](decisions/0002-feasibility-spike-first.md)). The system is currently a command-line pipeline that reads and writes files. The web application described under "After the gate" is built only if the spike ends in a "go".

## Spike pipeline (current)
A Python CLI package in `pipeline/` (ADR 0006, proposed). Each stage is a separate module that reads and writes versioned JSONL, so a failure can be traced to one stage.

```text
Regulations.gov API (read-only)
  -> 1. Docket shortlist          candidate EPA dockets with comment counts, attachment types, RTC availability
  -> 2. Fetch and freeze          raw API JSON + files, SHA-256 hashes, manifest (ADR 0007)
  -> 3. Text extraction           PyMuPDF; pages with no text layer excluded; page + offset locators
  -> 4. Near-duplicate collapse   MinHash; one representative per cluster, all member IDs kept (ADR 0008)
  -> 5. Extraction                claims and recommendations with verbatim spans
  -> 6. Canonicalization          group equivalent occurrences
  -> 7. Candidate retrieval       embeddings + issue filters, high recall (ADR 0004)
  -> 8. Pair classification       six spike labels (ADR 0010), with abstention
  -> 9. Evaluation                metrics, error analysis, cost and stability report
```

"RTC" is the agency's response-to-comments document.

| Piece | Where it runs | Notes |
|-------|---------------|-------|
| Source data | Regulations.gov API v4 | Public data. Requires an api.data.gov key from the environment. The client throttles to the published rate limits (DS-06). |
| Frozen dataset | `data/` on the developer machine | Raw and extracted data is gitignored. Only manifests are committed. |
| LLM inference | AWS Bedrock (open-weight models) or a local runtime (Ollama/vLLM) | Chosen by configuration through one client interface (ADR 0003, ADR 0005). Claude may be used during the pilot (ADR 0012). |
| Embeddings | Local, CPU (sentence-transformers class) | ADR 0004 (proposed). |
| Annotation | To be decided (AM-10; Label Studio recommended) | Self-hostable. Must be permitted on the network. |

**Blocker:** AWS Bedrock account access is pending (D-05). Until it arrives, model selection (MI-01) and any run that counts toward the gate are blocked. Whether to develop against a local model in the meantime is still open (MI-04).

## Portability
D-01 requires that the app can be hosted on local hardware, not only in AWS. Rules that follow from that:
- Model access goes through the client interface that doesn't depend on the provider. No pipeline code calls Bedrock directly.
- The app reads configuration and secrets from environment variables. In AWS, Secrets Manager injects them. Locally, they come from `.env`.
- AWS-specific services (S3, RDS, ECS) are deployment choices kept behind configuration, not dependencies in the app code.
- The local hardware envelope is still unknown (MI-05). It determines the largest feasible model and the cost projection.

## After the gate (provisional, not yet built)
The SiLab spec §4.8 proposes PostgreSQL (optionally pgvector) with relational entity and link tables instead of a graph database, Python processing jobs, and FastAPI query endpoints. The UI is still open: Streamlit with Cytoscape.js (§4.8) or a small React app (ADR 0001). See §9.8.

### Local development (after the gate)
Everything runs in Docker Compose:
- `db`: PostgreSQL 16
- `backend`: FastAPI (served by uvicorn) on port 8000
- `frontend`: dev server on port 5173

### Target AWS architecture (after the gate)
| Piece | AWS service | What it does |
|-------|-------------|--------------|
| Frontend hosting | S3 + CloudFront | S3 stores the built frontend files; CloudFront serves them fast over HTTPS. |
| Backend | ECS on Fargate, behind an Application Load Balancer | Runs the FastAPI Docker container without managing servers; the load balancer routes web traffic to it. |
| Container images | ECR | Private registry for the backend's Docker images. |
| Database | RDS for PostgreSQL | Managed Postgres with backups, in private subnets the internet can't reach. |
| Documents | S3 | Original comment files and extracted text (SiLab §4.8). |
| Model inference | Bedrock | Serves open-weight models through an API (ADR 0003). |
| Secrets | Secrets Manager | Database password and other secrets, injected into the backend as environment variables at runtime. |
| Logs and metrics | CloudWatch | Application logs and basic monitoring. |
| Networking | VPC | The private network all of the above lives in. |
| Infrastructure as code | Terraform (AWS provider) | Defines all of the above in code in `infra/`. |
| Terraform state | S3 (with state locking) | Stores Terraform's record of what it has created. Kept remotely, never in the repo. |

To be confirmed in an ADR before the deployment spec is written. A locally hosted deployment would replace these services with their Docker Compose equivalents.

### Terraform state
Terraform keeps a *state file* that maps the code in `infra/` to the real AWS resources it manages. State can contain sensitive values (such as generated passwords), so it is never committed to git. It is stored remotely in an S3 bucket with versioning and encryption enabled, and Terraform's S3 backend state locking (`use_lockfile = true`) prevents two people or processes from changing infrastructure at the same time. The state bucket itself is created once, by hand or by a small bootstrap configuration, before the main configuration is initialized.

## Environments
- **local:** developer machine (spike pipeline now; Docker Compose after the gate)
- **dev:** AWS (to be created; during the spike, Bedrock access only)
- **prod:** AWS or locally hosted (to be decided after the gate)
