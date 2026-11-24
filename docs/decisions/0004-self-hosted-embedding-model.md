# ADR 0004: Self-hosted open embedding model

- **Status:** Proposed
- **Date:** 2026-11-24
- **Register:** MI-03

## Context
Candidate retrieval (SiLab §4.8, §7.6 step 3) needs embeddings. Some Bedrock-hosted embedding models are proprietary, which conflicts with ADR 0003.

## Decision
Use a self-hosted, open-source embedding model (sentence-transformers class) from the start.

## Consequences
- It runs on CPU, so retrieval work can start before Bedrock access arrives (D-05).
- There's no proprietary dependency, and the same model runs locally and in AWS.
- Retrieval quality depends on a smaller model. Retrieval recall must be measured (SiLab §6.3), not assumed.

## Alternatives considered
- Bedrock-hosted embeddings: some are proprietary and they need Bedrock access.
