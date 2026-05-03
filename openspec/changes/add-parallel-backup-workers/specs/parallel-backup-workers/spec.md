## ADDED Requirements

### Requirement: Worker concurrency is configurable and bounded
The system SHALL allow file backup work to run with a configurable worker count and SHALL preserve the current single-threaded behavior when the worker count is `1`.

#### Scenario: Default worker configuration
- **WHEN** the user does not enable additional worker concurrency
- **THEN** the backup runs with the existing single-worker behavior

#### Scenario: Multiple workers enabled
- **WHEN** the user configures a worker count greater than `1`
- **THEN** the system processes multiple independent Dropbox files concurrently
- **THEN** the number of in-flight file operations remains bounded by the configured worker count and queue design

### Requirement: Concurrent backups preserve state correctness
The system SHALL keep backup state updates correct and free from write races while multiple workers are active.

#### Scenario: Two workers finish near the same time
- **WHEN** multiple workers complete successful file uploads concurrently
- **THEN** the system serializes or otherwise safely coordinates state updates
- **THEN** the state file remains valid and contains both completed files

#### Scenario: One worker fails while others succeed
- **WHEN** one concurrent file backup fails while other workers complete successfully
- **THEN** the failed file is reported without stopping unrelated in-flight file work
- **THEN** successfully completed files are still marked backed up

### Requirement: Run summaries remain accurate under concurrency
The system SHALL report total, skipped, backed-up, and failed counts accurately when file work is processed concurrently.

#### Scenario: Mixed concurrent outcomes
- **WHEN** a concurrent backup run includes skipped files, successful uploads, and failures
- **THEN** the final summary reflects the correct count for each outcome
