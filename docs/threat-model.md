# Threat Model

## Protected assets

- source-code integrity
- build and release credentials
- SWR image integrity
- CCE cluster credentials
- database credentials and customer order data
- Terraform state

## Trust boundaries

1. Developer workstation to GitHub
2. GitHub or CodeArts runner to SWR
3. SWR to CCE
4. Ingress to application pods
5. Orders service to catalog service
6. Application pods to databases
7. CCE and custom metrics to AOM

## Principal threats and controls

| Threat | Control |
|---|---|
| Secret committed to Git | ignore rules, secret scan, immediate rotation |
| Malicious dependency | dependency review, vulnerability scan, pinned ranges |
| Tampered image | private SWR, immutable tag, digest evidence |
| Privileged container | non-root, dropped capabilities, read-only root |
| Lateral movement | namespace separation and NetworkPolicy |
| Unreviewed production change | protected environment approval |
| Broken release | probes, smoke test, Helm atomic rollback |
| Resource exhaustion | requests, limits, HPA, AOM alarms |
| Lost Terraform state | protected remote backend before production use |

## Residual risks

- The reference application uses automatic table creation rather than managed
  migrations.
- A real production platform should use a managed database and protected remote
  Terraform state.
- Image signing and admission verification are roadmap items.
- NetworkPolicy behavior depends on the selected CCE networking implementation.

