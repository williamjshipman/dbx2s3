## ADDED Requirements

### Requirement: Delete synchronization is opt-in
The system SHALL only delete remote backup objects for Dropbox paths missing from the current account state when delete synchronization is explicitly enabled.

#### Scenario: Delete sync disabled
- **WHEN** a previously backed-up Dropbox file has been deleted from Dropbox and delete synchronization is not enabled
- **THEN** the system does not delete the remote object
- **THEN** the existing non-destructive backup behavior is preserved

#### Scenario: Delete sync enabled
- **WHEN** delete synchronization is enabled and a previously tracked Dropbox file is not observed during a successful full enumeration
- **THEN** the system treats that path as a deletion candidate for remote cleanup

### Requirement: Successful deletion updates both storage and local state
The system SHALL remove the remote object before removing the corresponding local backup state for a deleted Dropbox path.

#### Scenario: Remote deletion succeeds
- **WHEN** a deletion candidate is processed and the remote storage backend deletes the object successfully
- **THEN** the system removes the local state entry for that Dropbox path
- **THEN** the run summary records the deleted item

#### Scenario: Remote deletion fails
- **WHEN** a deletion candidate cannot be removed from remote storage
- **THEN** the system preserves the local state entry for that Dropbox path
- **THEN** the failure is reported so it can be retried on a later run

### Requirement: Partial Dropbox runs do not trigger deletion sync
The system SHALL skip delete synchronization when Dropbox enumeration does not complete successfully.

#### Scenario: Enumeration fails before completion
- **WHEN** Dropbox listing aborts before the backup has observed the full file set for the requested scope
- **THEN** the system does not delete any remote objects for unseen paths during that run
