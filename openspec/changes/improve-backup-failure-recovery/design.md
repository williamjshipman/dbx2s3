## Context

The backup loop currently increments an error count and continues when a file fails. That keeps runs resilient, but users lose the exact set of failed paths once logs rotate, and they must rerun a full account backup to retry a small subset of failures. A durable failure report and targeted retry mode close that operational gap.

## Goals / Non-Goals

**Goals:**
- Persist enough detail about file-level failures to support user follow-up.
- Add a retry mode that scopes work to unresolved failed paths.
- Clear entries from the failure report once a retry succeeds.
- Keep failure handling compatible with existing incremental state behavior.

**Non-Goals:**
- Implementing chunk-level resume for partial large-file transfers.
- Building a remote control plane or notification system.
- Replacing existing logs with the failure report.

## Decisions

1. **Persist failures in a structured local report.**  
   A JSON report stored near the state file keeps the feature dependency-free and easy to inspect. The report will record Dropbox path, stage, error message, and timestamp.

2. **Retry mode will target paths from the report instead of re-enumerating the entire account.**  
   This is the main user value: recovering only failed work. If the failure report is missing or empty, retry mode exits cleanly with a clear message.

3. **Remove resolved entries incrementally.**  
   Successful retries should clear only the paths that completed so partially resolved reports remain actionable.

4. **Keep file-level failures non-fatal to the overall run.**  
   The normal backup behavior of continuing after individual file errors remains intact; the new capability adds observability and targeted recovery rather than changing that contract.

## Risks / Trade-offs

- **[Failure report drift]** → Update the report atomically after each failure and each successful retry.
- **[Stale retries after files change]** → Reuse the normal backup state and Dropbox metadata checks when retrying failed paths.
- **[Operator confusion between logs and report]** → Document the report path and summary output clearly.

## Migration Plan

1. Add a failure-report persistence helper and wire it into file-level error handling.
2. Add a CLI/config entry point for retrying unresolved failed paths.
3. Update summaries to point users to the report and remaining failure count.
4. Add tests for report persistence, targeted retries, and partial recovery.

Rollback is simple: stop writing the report and remove the retry-only mode. Existing state tracking remains unchanged.

## Open Questions

- Should retry mode accept only the default failure report path, or allow an explicit path override?
- Should the failure report be kept indefinitely or pruned automatically after a fully successful run?
