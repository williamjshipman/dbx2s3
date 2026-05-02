## Why

When individual files fail during backup, the tool logs the error but gives users no durable list of failed files and no targeted way to retry only those failures. That makes follow-up recovery clumsy for large Dropbox accounts where rerunning the entire backup is unnecessarily expensive.

## What Changes

- Persist a structured failure report for file-level backup failures.
- Add a retry mode that retries only the paths recorded in the failure report.
- Remove paths from the failure report as they succeed on later retries.
- Improve run summaries so users can quickly identify unresolved failures.

## Capabilities

### New Capabilities
- `backup-failure-recovery`: Persist failed-file details and support targeted retries of unresolved failures.

### Modified Capabilities

None.

## Impact

- Affected code: `src/dbx2s3/backup.py`, `src/dbx2s3/cli.py`, `src/dbx2s3/config.py`, `src/dbx2s3/state_manager.py` or a new failure-report helper
- Affected docs: README, troubleshooting, examples
- Affected tests: backup orchestration and retry-mode unit tests
