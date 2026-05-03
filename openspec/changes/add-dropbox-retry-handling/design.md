## Context

The backup flow depends on Dropbox listing and download calls completing on the first attempt. Real Dropbox accounts can hit transient transport failures, service-side timeouts, or explicit rate limiting. The current implementation logs the failure and moves on, which is acceptable for permanent errors but not for short-lived Dropbox API failures.

## Goals / Non-Goals

**Goals:**
- Retry retryable Dropbox list and download failures automatically.
- Respect explicit server retry delays for rate-limited requests.
- Keep retry behavior bounded and configurable.
- Preserve immediate failure for non-retryable errors such as invalid credentials or authorization issues.

**Non-Goals:**
- Adding retries for every storage backend operation in this change.
- Implementing distributed rate limiting across multiple machines.
- Changing the default single-process architecture of the backup tool.

## Decisions

1. **Centralize retry logic in the Dropbox client.**  
   Retry behavior belongs where Dropbox API exceptions are interpreted, so callers continue to receive a simple iterator/download interface. The alternative—retrying in `BackupManager`—would duplicate classification logic across listing and download paths.

2. **Use bounded exponential backoff with jitter and optional server delay override.**  
   The client will use a configurable maximum attempt count and base delay. When Dropbox exposes a retry delay, that value takes precedence; otherwise the client uses exponential backoff with jitter to avoid synchronized retries.

3. **Treat authentication and authorization failures as non-retryable.**  
   Invalid credentials, revoked tokens, and permanent path validation failures should fail immediately because retries do not improve the outcome.

4. **Expose retry settings through configuration.**  
   Retry count and base delay will be configured from environment variables so operators can tune them for home or hosted environments without code changes.

## Risks / Trade-offs

- **[Longer runtime during outages]** → Bound retries with configurable attempt limits and log each retry decision.
- **[Incorrectly retrying permanent failures]** → Maintain an explicit allowlist of retryable Dropbox exception types/statuses.
- **[Insufficient observability]** → Include attempt number, operation, and delay in retry logs so users can understand slow runs.

## Migration Plan

1. Add configuration for retry settings with safe defaults.
2. Implement retry helpers in the Dropbox client for list and download operations.
3. Add tests for transient failures, rate limits, and permanent failures.
4. Document the new behavior and tuning options.

Rollback is low risk: revert to single-attempt behavior by removing the retry wrapper or setting max attempts to `1`.

## Open Questions

- Which Dropbox exception types expose structured retry delay information in the SDK version used here?
- Should the same retry policy be reused later for S3 and Azure operations, or stay Dropbox-specific?
