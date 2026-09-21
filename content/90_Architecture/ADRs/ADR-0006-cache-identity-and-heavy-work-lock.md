---
id: ADR-0006
type: adr
title: Reuse exact blob digests and serialize machine-heavy work
status: accepted
owner: capabilities
created: '2026-09-17T00:00:00.000Z'
updated: '2026-09-17T00:00:00.000Z'
tags: [adr, cache, reproducibility, operations]
summary: Share file digests only for byte-identical tracked Git blobs and coordinate resource-heavy commands with an advisory machine-wide lock.
---

## Context

Parallel worktrees repeatedly hash identical tracked files, while concurrent
indexing, builds, snapshots and full tests can exhaust disk and memory. A
worktree path or inode is not a stable identity, and serialization must not
alter the command's inputs or outputs.

## Decision

Use Git blob identity as a reusable digest index only when the tracked
worktree bytes are known to match the blob and checkout transformations cannot
change those bytes. Do not reuse for untracked or transformed files. Keep the
existing digest formula unchanged. Wrap designated heavy tasks in one advisory
machine-wide lock that reports its holder and wait; read-only work and
unrelated small checks do not acquire it.

## Alternatives considered

- Per-worktree path/inode caches miss reuse across fresh worktrees.
- Reusing by path or commit risks stale content and needlessly broad
  invalidation.
- Running heavy commands concurrently can exhaust shared machine resources.

## Consequences

Cache hits must be auditable and may be rejected if Git cannot prove the byte
mapping. The lock coordinates cooperating processes only; it is not a
correctness or isolation boundary for unrelated tools.

## Evidence and limits

PR #51 (`649be7f`) records reuse of 166 of 169 tracked file digests across two
commits and adds the blob-digest index and heavy-work wrapper in
`packages/capabilities/src/capcov/artifacts.py` and
`packages/capabilities/scripts/with-heavy-lock.py`. The digest formula was
unchanged. This is exact tracked-blob digest reuse, not a campaign, verdict,
checker-result, or observation cache. The measured index does not help
predominantly untracked oracle trees, and the lock does not reclaim reachable
generated artifacts in Git history. The 166-of-169 result is historical PR
evidence and was not rerun for this ADR publication.
