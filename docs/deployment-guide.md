# Huawei Cloud Deployment Guide

## 1. Prepare Huawei Cloud

Confirm region availability, quotas, and pricing for:

- VPC and subnet
- CCE cluster and worker nodes
- SWR
- AOM custom metrics
- load balancer or ingress
- managed PostgreSQL, when used

Terraform can provision the VPC, subnet, CCE cluster, node pool, and private SWR
repositories. Review every plan before applying it.

## 2. Prepare SWR

Create or confirm:

- one private SWR organization
- `catalog-service` repository
- `orders-service` repository
- least-privilege push credentials for the build pipeline
- least-privilege image pull access for CCE

Use immutable semantic-version or commit-SHA tags.

## 3. Prepare CCE

Create the namespaces:

```bash
kubectl create namespace commerce-dev
kubectl create namespace commerce-staging
kubectl create namespace commerce-prod
```

Install and configure:

- NGINX ingress, when public routing is required
- metrics server for HPA
- Cloud Native Cluster Monitoring connected to AOM

## 4. Create runtime secrets

Create the database URLs through an approved secret-management process. The
example below is intentionally incomplete:

```bash
kubectl -n commerce-dev create secret generic commerce-platform-secrets \
  --from-literal=catalog-database-url='REDACTED' \
  --from-literal=orders-database-url='REDACTED'
```

Do not place the resulting Secret YAML in GitHub.

## 5. Configure GitHub environments

Create `development`, `staging`, and `production` environments. Protect the
production environment with a required reviewer.

Required encrypted secrets:

| Secret | Purpose |
|---|---|
| `SWR_REGISTRY` | regional SWR registry hostname |
| `SWR_ORGANIZATION` | private SWR organization |
| `SWR_USERNAME` | pipeline login user |
| `SWR_PASSWORD` | pipeline login secret |
| `CCE_KUBECONFIG_BASE64` | protected CCE kubeconfig |

Prefer CodeArts service endpoints and credential management when CodeArts is the
release orchestrator.

## 6. Deploy

Run the `Build and Deploy to Huawei Cloud` workflow with an immutable tag.
The Helm command uses `--atomic`, so a failed upgrade is rolled back.

Verify:

```bash
kubectl -n commerce-prod get deploy,pod,svc,ingress,hpa,pdb
kubectl -n commerce-prod rollout status deploy/commerce-platform-commerce-platform-catalog
kubectl -n commerce-prod rollout status deploy/commerce-platform-commerce-platform-orders
```

Confirm actual generated resource names with `helm list` and `kubectl get`
instead of assuming names in automation.

