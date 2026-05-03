## 1. Storage and configuration changes

- [ ] 1.1 Extend the storage interface and first-party backends with object deletion support.
- [ ] 1.2 Add opt-in delete sync configuration and CLI plumbing with safe defaults.

## 2. Backup orchestration

- [ ] 2.1 Track the set of Dropbox paths seen during a successful enumeration for the requested scope.
- [ ] 2.2 Delete remote objects for tracked-but-missing paths only after enumeration completes successfully.
- [ ] 2.3 Preserve local state when remote deletion fails and include deletion counts in the run summary.

## 3. Validation and docs

- [ ] 3.1 Add unit tests for delete sync enabled, disabled, and failed-enumeration behavior.
- [ ] 3.2 Document delete sync safeguards and operator expectations.
