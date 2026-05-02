## ADDED Requirements

### Requirement: Dropbox operations retry transient failures
The system SHALL retry Dropbox file listing and file download operations when they fail with retryable transient API or network errors, up to a configured maximum attempt count.

#### Scenario: Listing succeeds after a transient failure
- **WHEN** Dropbox file enumeration fails with a retryable error before succeeding on a later attempt
- **THEN** the system retries the enumeration operation
- **THEN** the backup continues without requiring a new full run

#### Scenario: Download succeeds after a transient failure
- **WHEN** downloading a Dropbox file fails with a retryable error and a later attempt succeeds within the configured attempt limit
- **THEN** the system retries the download
- **THEN** the file is uploaded and marked backed up once the successful download completes

#### Scenario: Permanent Dropbox failure does not retry
- **WHEN** Dropbox returns a non-retryable error such as invalid credentials or insufficient access
- **THEN** the system does not retry the operation
- **THEN** the failure is surfaced immediately to the caller or file-level error handler

### Requirement: Dropbox rate limits are honored
The system SHALL honor Dropbox rate-limit retry delays when provided and SHALL otherwise use bounded exponential backoff with jitter between retry attempts.

#### Scenario: Server retry delay is available
- **WHEN** Dropbox indicates that a request is rate limited and provides a retry delay
- **THEN** the next retry waits at least that delay before reissuing the request

#### Scenario: No server delay is available
- **WHEN** a retryable Dropbox failure occurs without an explicit retry delay
- **THEN** the system waits using the configured exponential backoff policy before retrying
