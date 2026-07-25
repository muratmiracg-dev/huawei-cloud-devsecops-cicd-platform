# Contributing

## Development flow

1. Create a short-lived branch from `main`.
2. Install the development dependencies.
3. Make a focused change.
4. Run `make verify`.
5. Update documentation and tests.
6. Open a pull request using the repository template.

## Commit style

Use concise, outcome-oriented messages:

- `Add inventory reservation endpoint`
- `Harden CCE workload security context`
- `Document AOM alert thresholds`

## Pull-request expectations

- no credentials or populated secret files
- tests for changed behavior
- rollback notes for deployment changes
- screenshots only when they demonstrate an actual result
- no claim that a Huawei Cloud deployment succeeded without evidence

