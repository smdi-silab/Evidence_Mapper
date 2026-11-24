# ADR 0011: Data handling, logging, and prompt-injection controls

- **Status:** Proposed
- **Date:** 2026-11-24
- **Register:** SP-01, SP-02, SP-04

## Context
Public comments are public record, but they still contain names, addresses, and sometimes health details. Any submission can contain text written to manipulate a model (SiLab §4.7). These rules apply from the first line of code.

## Decision
- **Logging (SP-01):** Logs hold IDs, hashes, token counts, timings, and errors only. Full comment text lives only in the frozen dataset store and the output JSONL, and both are access-controlled.
- **Prompt injection (SP-02):** Source text goes inside clearly delimited data blocks, and the model has no tools in the pipeline. Every output is schema-validated (ADR 0005, ADR 0009). Every quoted span is verified against the source (AM-09). The challenge set includes a few injected test passages.
- **Credentials (SP-04):** The api.data.gov key and AWS credentials come from the environment or a secrets manager and are never committed. Claude Code doesn't read or print secret files.

## Consequences
- Debugging extraction means opening the frozen store by ID, not reading logs.
- Injection attempts can at worst produce schema-valid but wrong output, which span verification and evaluation are designed to catch.

## Alternatives considered
- Logging full prompts and outputs: easier to debug, but spreads personal data into logs.
- Prompt instructions alone against injection: not a reliable control.
