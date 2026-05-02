## 1. Concurrency plumbing

- [ ] 1.1 Add worker-count configuration with a default that preserves current single-threaded behavior.
- [ ] 1.2 Refactor per-file backup handling into a worker-friendly unit of work.

## 2. Safe concurrent execution

- [ ] 2.1 Add a bounded worker pool for file backup operations after Dropbox enumeration.
- [ ] 2.2 Serialize or otherwise coordinate state writes and shared summary counters safely across workers.

## 3. Validation and docs

- [ ] 3.1 Add tests for concurrent success, failure isolation, and accurate summary accounting.
- [ ] 3.2 Document concurrency limits, defaults, and tuning guidance.
