## Why

Dropbox API backups are currently vulnerable to transient network failures and rate limiting. A single temporary Dropbox error can leave a backup incomplete even when a retry moments later would succeed.

## What Changes

- Add bounded retry handling for Dropbox file listing and file download operations.
- Add explicit rate-limit handling that honors Dropbox-provided retry delays when available.
- Expose retry settings so operators can tune attempt count and backoff behavior without code changes.
- Document retry behavior and add tests for retryable and non-retryable failures.

## Capabilities

### New Capabilities
- `dropbox-retry-handling`: Retry transient Dropbox API failures and rate limits during enumeration and download.

### Modified Capabilities

None.

## Impact

- Affected code: `src/dbx2s3/dropbox_client.py`, `src/dbx2s3/config.py`, `src/dbx2s3/cli.py`
- Affected docs: `README.md`, troubleshooting and configuration docs
- Affected tests: Dropbox client and backup integration-style unit tests
