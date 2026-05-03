## Context

Today the backup is append/update only. That is safe for archival use, but some users want the backup destination to reflect the current contents of Dropbox. Achieving this safely requires comparing the set of tracked files to the set observed during a successful enumeration and deleting only when the user explicitly enables that behavior.

## Goals / Non-Goals

**Goals:**
- Add an opt-in delete sync mode that removes remote objects no longer present in Dropbox.
- Avoid deleting anything unless the current run completed Dropbox enumeration successfully.
- Keep local state aligned with remote storage after successful deletions.
- Surface deletion failures without silently dropping state.

**Non-Goals:**
- Enabling destructive delete sync by default.
- Versioned retention or recycle-bin behavior in this change.
- Folder placeholder synchronization for providers that do not model folders as objects.

## Decisions

1. **Make delete sync explicitly opt-in.**  
   The current behavior is non-destructive and safer as a default. Users who want mirroring can enable delete sync through configuration or CLI.

2. **Compare tracked state to the set seen during a successful enumeration.**  
   The state file already tracks backed-up Dropbox paths. After a full enumeration completes, the backup process can compute `tracked - seen_this_run` to find deletion candidates. This avoids requiring a full remote listing from S3.

3. **Delete remote objects before removing state.**  
   State will only be removed after the remote delete succeeds so failed deletions remain retryable on the next run.

4. **Add delete support to the storage interface.**  
   Delete sync requires a backend-level delete primitive so S3 and Azure can implement provider-specific removal behavior consistently.

## Risks / Trade-offs

- **[Accidental destructive behavior]** → Keep delete sync off by default and require an explicit flag/config value.
- **[False-positive deletions from partial runs]** → Only evaluate delete candidates after Dropbox enumeration completes successfully.
- **[Backend capability mismatch]** → Add delete support to all first-party storage backends before exposing the feature.

## Migration Plan

1. Extend the storage abstraction with object deletion.
2. Track the set of paths seen during a successful backup run.
3. Add opt-in delete sync orchestration and reporting.
4. Add tests and documentation covering destructive behavior and safeguards.

Rollback is straightforward: disable delete sync and stop invoking backend deletes. Existing objects remain intact.

## Open Questions

- Should delete sync be controlled only by configuration, or also by a dedicated CLI flag?
- Should a future dry-run mode share the same deletion planning logic?
