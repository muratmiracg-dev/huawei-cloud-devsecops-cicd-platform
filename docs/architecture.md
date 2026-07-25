# Architecture

## Runtime view

```mermaid
flowchart TD
    U["API consumer"] --> I["CCE ingress / load balancer"]
    I --> C["Catalog service"]
    I --> O["Orders service"]
    O --> C
    C --> CD[("Catalog PostgreSQL")]
    O --> OD[("Orders PostgreSQL")]
    C --> M["AOM / Prometheus"]
    O --> M
```

## Delivery view

```mermaid
flowchart TD
    G["GitHub source"] --> Q["Quality and security gates"]
    Q --> B["CodeArts or GitHub build"]
    B --> S["Private SWR repositories"]
    S --> D["CCE development"]
    D --> A{"Release approval"}
    A --> P["CCE production"]
    P --> O["AOM verification"]
    O -->|healthy| R["Release complete"]
    O -->|unhealthy| X["Atomic rollback"]
```

## Design decisions

- GitHub is the public, reviewable source-of-truth.
- CodeArts is the Huawei-native production release option.
- Docker images are immutable and stored privately in SWR.
- Helm provides repeatable environment-specific releases.
- Database credentials are referenced from an existing Kubernetes Secret.
- Workloads run as a non-root user with a read-only root filesystem.
- NetworkPolicy limits inbound and outbound workload traffic.
- AOM and Prometheus-compatible metrics provide operational feedback.

## Environment separation

| Environment | Namespace | Deployment | Purpose |
|---|---|---|---|
| Development | `commerce-dev` | automatic | fast integration feedback |
| Staging | `commerce-staging` | automatic after gates | production-like validation |
| Production | `commerce-prod` | protected approval | controlled release |

