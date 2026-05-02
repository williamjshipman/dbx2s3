## ADDED Requirements

### Requirement: File-level failures are persisted
The system SHALL persist a structured local report for file-level backup failures so users can review unresolved paths after a run completes.

#### Scenario: File upload fails during a normal run
- **WHEN** a Dropbox file cannot be backed up because download, upload, or state-update handling fails for that file
- **THEN** the system records the Dropbox path, failure stage, error details, and timestamp in the failure report
- **THEN** the run summary indicates that unresolved failures were recorded

#### Scenario: No file-level failures occur
- **WHEN** a backup run completes without file-level failures
- **THEN** the system leaves no unresolved entries in the failure report for that run scope

### Requirement: Users can retry unresolved failures without a full backup run
The system SHALL provide a retry mode that processes only unresolved failed paths from the failure report.

#### Scenario: Retry mode has unresolved paths
- **WHEN** the user starts the backup in retry mode and the failure report contains unresolved paths
- **THEN** the system attempts backup only for those paths
- **THEN** it applies the normal backup rules for download, upload, and state updates to each retried path

#### Scenario: Retry mode has no unresolved paths
- **WHEN** the user starts retry mode and there are no unresolved failed paths to process
- **THEN** the system exits without running a full Dropbox enumeration
- **THEN** it reports that there is nothing to retry

### Requirement: Successful retries clear resolved failures
The system SHALL remove a path from the failure report once that path is backed up successfully in retry mode or a later normal run.

#### Scenario: Retry succeeds for one of several failures
- **WHEN** the failure report contains multiple unresolved paths and one path succeeds on retry
- **THEN** the successful path is removed from the unresolved failure list
- **THEN** other unresolved paths remain in the report
