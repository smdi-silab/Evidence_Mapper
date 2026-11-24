# ADR 0003: Open-weight models, runnable on Bedrock or local hardware

- **Status:** Accepted
- **Date:** 2026-11-24
- **Register:** D-01

## Context
If the app is adopted, it may need to be hosted locally rather than in AWS. The SiLab spec assumed "an approved Bedrock model" for extraction and classification (§4.8, §7.6, §9.7). Proprietary Bedrock models can't be run outside AWS.

AWS Bedrock is a managed AWS service that serves foundation models through an API, so we don't run GPU servers ourselves.

## Decision
- Every model in the pipeline must be **open-weight**, **available on AWS Bedrock** for development, and **hostable on local hardware without code changes**. This includes the embedding model (see ADR 0004).
- This amends SiLab §4.8, §7.6, and §9.7: "approved Bedrock model" now means "open-weight model available on Bedrock and locally hostable".

## Consequences
- Model choice is limited to Bedrock's open-weight catalog (MI-01, blocked on Bedrock access, D-05). Proprietary Bedrock models are excluded.
- Code must reach models through a client interface that doesn't depend on the provider (ADR 0005), so switching between Bedrock and a local runtime is a matter of configuration.
- The local hardware available (MI-05, open) limits which model sizes are worth testing.
- Bedrock and local runs need a parity check before results are trusted across runtimes (MI-06).
- Licenses must be checked. Some open-weight licenses, such as Llama's, have custom terms.

## Alternatives considered
- Any approved Bedrock model, including proprietary ones: rejected because it can't be hosted locally.
- Local-only from the start: rejected because no local hardware is confirmed yet (MI-05) and Bedrock gives fast access to several model sizes.
