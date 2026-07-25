# CodeArts Setup

## Required service endpoints

Configure endpoints for:

- GitHub repository
- Huawei SWR
- CCE Kubernetes cluster

Use named credentials stored by CodeArts. Do not paste credentials into build
scripts, variables committed to Git, or screenshots.

## Suggested pipeline

| Stage | Gate | Output |
|---|---|---|
| Source | protected branch | immutable commit SHA |
| Check | Ruff and policy checks | quality report |
| Test | 75% minimum coverage | test and coverage report |
| Build | reproducible Dockerfile | two local images |
| Security | zero high/critical findings | scan and SBOM evidence |
| Publish | successful SWR authentication | immutable image digest |
| Deploy dev | Helm atomic upgrade | development release |
| Verify | health and smoke tests | release evidence |
| Approval | named production reviewer | audited decision |
| Deploy prod | Helm atomic upgrade | production release |
| Observe | AOM health gates | complete or rollback |

## Variables

Non-sensitive variables:

- `SWR_REGISTRY`
- `SWR_ORGANIZATION`
- `IMAGE_TAG`
- `TARGET_NAMESPACE`
- `HELM_VALUES_FILE`

Sensitive values belong in CodeArts credential management:

- SWR password/login secret
- Kubernetes credential
- Huawei Cloud access credentials

## Portfolio evidence

Capture:

- one successful pipeline
- one intentionally failed quality gate
- one blocked vulnerability
- SWR image versions
- CCE rollout
- AOM health verification
- rollback result

Redact tenant IDs, account identifiers, IP addresses, and secrets.

