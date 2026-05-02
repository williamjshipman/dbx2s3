## Context

Each Dropbox file backup is mostly independent: decide whether it needs backup, download it, upload it, then record state. That makes the workflow a good candidate for bounded worker concurrency. The main constraints are state-file safety, predictable memory use, and preserving the current file-level error isolation model.

## Goals / Non-Goals

**Goals:**
- Add configurable worker concurrency with a safe default that preserves current behavior.
- Bound in-flight file work to avoid unbounded memory growth.
- Keep state updates correct and race-free.
- Preserve clear summary accounting for total, skipped, backed-up, and failed files.

**Non-Goals:**
- Distributed or multi-host backup execution.
- Parallel multipart upload orchestration within a single file transfer.
- Replacing the current state file with an external database.

## Decisions

1. **Use a bounded worker pool with default worker count of 1.**  
   This preserves current semantics for existing users while allowing opt-in speed improvements. A bounded queue keeps memory usage tied to worker count rather than Dropbox account size.

2. **Keep Dropbox listing single-threaded and dispatch file work to workers.**  
   Enumeration already provides a stable stream of file metadata. The main parallelism opportunity is the per-file backup pipeline after listing.

3. **Serialize state writes behind a synchronization boundary.**  
   The JSON state file is not safe for concurrent writes. Workers can perform skip/download/upload work concurrently, but successful state updates must be serialized or funneled through a dedicated writer.

4. **Maintain per-file failure isolation and aggregate counters centrally.**  
   Worker exceptions should not terminate the entire run. Shared stats and reporting need thread-safe aggregation.

## Risks / Trade-offs

- **[State corruption under concurrent writes]** → Serialize state mutations explicitly and test with concurrent success paths.
- **[Higher Dropbox/S3 pressure]** → Bound worker count and document conservative defaults.
- **[Harder debugging]** → Include file path and worker context in logs and summaries.

## Migration Plan

1. Add worker-count configuration with default `1`.
2. Refactor per-file backup logic into a worker-friendly function.
3. Add safe synchronization for state updates and shared counters.
4. Add tests for concurrent success/failure accounting and document tuning guidance.

Rollback path: set worker count back to `1` or revert the worker-pool orchestration while retaining the single-threaded loop.

## Open Questions

- Should worker count be exposed only by environment variable or also by CLI flag?
- Is the current Dropbox SDK client safe to share across threads, or should each worker own its own client/session?
