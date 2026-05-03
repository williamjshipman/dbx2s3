## Why

The backup currently only adds or updates objects in remote storage. Files deleted from Dropbox remain in S3 and in the local state forever, which prevents the backup from acting as an accurate mirror when users want synchronization semantics.

## What Changes

- Add an explicit opt-in delete synchronization mode for files removed from Dropbox.
- Detect tracked files that were not seen during the current Dropbox enumeration.
- Delete corresponding remote objects and remove their saved state when deletion succeeds.
- Report deletion results so users can see what was removed and what failed.

## Capabilities

### New Capabilities
- `dropbox-delete-sync`: Synchronize Dropbox deletions to the remote backup destination when delete sync is enabled.

### Modified Capabilities

None.

## Impact

- Affected code: `src/dbx2s3/backup.py`, `src/dbx2s3/storage.py`, `src/dbx2s3/s3_storage.py`, `src/dbx2s3/config.py`, `src/dbx2s3/cli.py`, `src/dbx2s3/state_manager.py`
- Affected docs: README, quickstart, troubleshooting
- Affected tests: backup orchestration, state handling, storage backend tests
