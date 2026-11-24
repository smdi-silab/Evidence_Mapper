# ADR 0012: Where comment data may be sent during the spike

- **Status:** Accepted
- **Date:** 2026-11-24
- **Register:** SP-03 (decided); related to MP-01, D-04

## Context
SP-03 asked whether comment data may go to third-party hosted model APIs during development. The register also planned to run the manual pilot through Claude in chat (MP-01) and to have Claude (chat) analyze results (D-04). Both send comment text to Anthropic.

## Decision
Because this is a pilot, comment data may be sent to **Claude (Anthropic)** as needed, in addition to local runtimes and AWS Bedrock. Any other third-party hosted model API needs the project lead's approval first.

## Consequences
- MP-01 (Claude plus a local open-weight model) and D-04 can go ahead as written.
- Claude results never stand in for open-weight results and never count toward the gate (ADR 0003, MP-01).
- Revisit before any non-pilot or agency use.

## Alternatives considered
- Local only: would block the Claude pass in the manual pilot and Claude-led analysis.
