# ADR 0008: Collapse campaign and near-duplicate comments

- **Status:** Proposed
- **Date:** 2026-11-24
- **Register:** DS-02

## Context
Campaign comments are many near-identical submissions. They inflate processing cost and can be mistaken for votes. SiLab §4.3 requires that occurrences are never discarded, and that occurrence counts are not treated as votes or as evidence of truth.

## Decision
- Detect near-duplicates with shingle/MinHash similarity **before extraction**.
- Process one representative per cluster.
- Keep every member's comment ID, so per-comment provenance and counts can be recovered (the §4.3 invariant).
- Never present cluster size as a vote.

## Consequences
- Lower model cost on campaign-heavy dockets.
- Holdout splits must keep each cluster on one side (AM-06).
- The similarity threshold affects results, so it must be recorded and checked by inspection.

## Alternatives considered
- (a) Exclude duplicates: breaks the §4.3 invariant.
- (c) Process every comment: wasteful, and over-weights campaigns in the evaluation sample.
