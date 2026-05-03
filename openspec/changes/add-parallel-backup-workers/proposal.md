## Why

The current backup loop is single-threaded, which is simple but slow for large Dropbox accounts with many independent files. Controlled concurrency would reduce wall-clock runtime while keeping the tool focused on direct Dropbox API to S3 backup.

## What Changes

- Add configurable worker-based concurrency for file backup operations.
- Keep bounded in-flight work so memory use remains predictable.
- Preserve per-file isolation so one worker failure does not stop the entire backup.
- Maintain correct state updates and summary reporting under concurrent execution.

## Capabilities

### New Capabilities
- `parallel-backup-workers`: Process multiple Dropbox files concurrently with configurable worker counts.

### Modified Capabilities

None.

## Impact

- Affected code: `src/dbx2s3/backup.py`, `src/dbx2s3/config.py`, `src/dbx2s3/cli.py`, `src/dbx2s3/state_manager.py`
- Affected docs: README and performance/tuning guidance
- Affected tests: backup orchestration and state-safety tests
