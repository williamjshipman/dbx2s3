## 1. Failure report persistence

- [ ] 1.1 Add a structured local failure report with atomic updates and clear path/location semantics.
- [ ] 1.2 Record file-level failures with path, stage, error details, and timestamp during normal backup runs.

## 2. Targeted retry workflow

- [ ] 2.1 Add a retry mode that loads unresolved paths from the failure report instead of enumerating the full Dropbox scope.
- [ ] 2.2 Remove resolved paths from the failure report after successful retries or later normal-run success.

## 3. Validation and docs

- [ ] 3.1 Add tests for failure report creation, empty retry mode, and partial retry recovery.
- [ ] 3.2 Document how users inspect and retry unresolved failures.
