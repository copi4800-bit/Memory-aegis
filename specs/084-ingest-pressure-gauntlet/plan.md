# Plan: 084 Ingest Pressure Gauntlet

## Intent

Turn the observed ingest-rejection signal into a measured part of the Aegis gauntlet.

## Workstreams

### 1. Ingest Scenarios

- Add a repetitive same-subject write-pressure case.
- Add a mixed-content write-pressure case if needed.

### 2. Artifact Shape

- Record accepted count, rejected/no-op count, and final recall state.
- Keep grouped reporting compatible with the current gauntlet summary.

### 3. Verification

- Run the updated gauntlet.
- Keep the full test suite green.
