# ADR 0005: Provider-agnostic model client with schema-validated output

- **Status:** Proposed
- **Date:** 2026-11-24
- **Register:** MI-02; interface part of MI-04

## Context
ADR 0003 requires the same pipeline code to run against Bedrock and against a local runtime such as Ollama or vLLM. The two support different ways of forcing structured (JSON) output. SiLab §6.4 and §6.5 track schema validity after bounded retries (target ≥ 99%).

## Decision
- All model calls go through one client interface that doesn't depend on the provider. Pipeline stages never call Bedrock or a local runtime directly.
- **On Bedrock:** validate each response against the Pydantic schema (ADR 0009), with a bounded number of retries.
- **Locally:** use constrained decoding, such as vLLM guided JSON.
- Log the schema-validity rate for each runtime.

## Consequences
- The differences between runtimes live inside adapters. This is how ADR 0003's "without code changes" requirement is met: the structured-output mechanism varies, but pipeline code doesn't.
- Development can start against a small local model before Bedrock access arrives. Whether to do so is still open (MI-04).
- The two mechanisms can produce different failure patterns, so the parity check (MI-06) should compare schema-validity rates.

## Alternatives considered
- Native JSON or tool mode only: not available on every runtime.
- One mechanism everywhere: constrained decoding isn't available on Bedrock.
