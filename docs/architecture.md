# Architecture

> Keep this document current. Update it whenever a spec changes the shape of the system.

## Overview
Evidence Mapper is a web application with a React frontend, a FastAPI backend, and a PostgreSQL database.

## Local development
Everything runs in Docker Compose:
- `db`: PostgreSQL 16
- `backend`: FastAPI (served by uvicorn) on port 8000
- `frontend`: Vite dev server on port 5173

## Target AWS architecture (proposed, not yet built)
| Piece | AWS service | What it does |
|-------|-------------|--------------|
| Frontend hosting | S3 + CloudFront | S3 stores the built React files; CloudFront serves them fast over HTTPS. |
| Backend | ECS on Fargate, behind an Application Load Balancer | Runs the FastAPI Docker container without managing servers; the load balancer routes web traffic to it. |
| Container images | ECR | Private registry for the backend's Docker images. |
| Database | RDS for PostgreSQL | Managed Postgres with backups, in private subnets the internet can't reach. |
| Secrets | Secrets Manager | Database password and other secrets, injected into the backend at runtime. |
| Logs and metrics | CloudWatch | Application logs and basic monitoring. |
| Networking | VPC | The private network all of the above lives in. |
| Infrastructure as code | Terraform (AWS provider) | Defines all of the above in code in `infra/`. |
| Terraform state | S3 (with state locking) | Stores Terraform's record of what it has created. Kept remotely, never in the repo. |

To be confirmed in an ADR before the deployment spec is written.

### Terraform state
Terraform keeps a *state file* that maps the code in `infra/` to the real AWS resources it manages. State can contain sensitive values (such as generated passwords), so it is never committed to git. It is stored remotely in an S3 bucket with versioning and encryption enabled, and Terraform's S3 backend state locking (`use_lockfile = true`) prevents two people or processes from changing infrastructure at the same time. The state bucket itself is created once, by hand or by a small bootstrap configuration, before the main configuration is initialized.

## Environments
- **local:** Docker Compose
- **dev:** AWS (to be created)
- **prod:** AWS (to be created)
