# Incident Response

## Severity

| Severity | Example | Target response |
|---|---|---:|
| SEV-1 | service unavailable or data integrity risk | 15 minutes |
| SEV-2 | major degradation or repeated failed orders | 30 minutes |
| SEV-3 | limited impact with workaround | next working session |

Targets are portfolio objectives, not an operational guarantee.

## Response lifecycle

1. Detect through AOM, a smoke test, or user report.
2. Classify severity and assign an incident owner.
3. Stabilize the platform; roll back when a release is implicated.
4. Preserve relevant logs, metrics, events, and image/commit identifiers.
5. Restore service and verify business operations.
6. Publish a concise incident timeline.
7. Complete a blameless postmortem with corrective actions.

## Minimum timeline fields

- detection time
- first response
- mitigation start
- recovery time
- affected service and environment
- release tag and commit SHA
- customer or business impact

