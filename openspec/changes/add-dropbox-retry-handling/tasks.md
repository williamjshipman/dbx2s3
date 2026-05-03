## 1. Configuration and retry policy

- [x] 1.1 Add retry-related configuration fields and environment variables for Dropbox operations.
- [x] 1.2 Implement a reusable retry helper in the Dropbox client with bounded exponential backoff and jitter.

## 2. Dropbox client integration

- [x] 2.1 Apply the retry helper to recursive listing and pagination continuation calls.
- [x] 2.2 Apply the retry helper to full-file and streaming download calls while preserving existing interfaces.

## 3. Validation and documentation

- [x] 3.1 Add unit tests covering retryable failures, non-retryable failures, and rate-limit delays.
- [x] 3.2 Document retry behavior and tuning options in user-facing docs.
