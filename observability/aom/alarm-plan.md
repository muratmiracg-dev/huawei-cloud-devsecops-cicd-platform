# Huawei AOM Monitoring and Alarm Plan

## Collection

Enable the CCE Cloud Native Cluster Monitoring add-on and connect it to the
selected AOM instance. Confirm cluster, node, workload, pod, event, and custom
application metrics before enabling production notifications.

The services expose Prometheus metrics at `/metrics`.

## Service-level indicators

| Signal | Metric or source | Initial objective |
|---|---|---:|
| Availability | readiness success | >= 99.9% |
| Error rate | HTTP 5xx / total requests | < 1% |
| Latency | HTTP request duration p95 | < 500 ms |
| Saturation | CPU and memory utilization | < 80% sustained |
| Recovery | pod/deployment events | < 10 minutes |

These are portfolio objectives, not measured production guarantees.

## Alarm rules

| Severity | Condition | Window | First action |
|---|---|---:|---|
| Critical | Ready replicas below minimum | 2 min | Check rollout and events |
| Critical | HTTP 5xx rate above 5% | 5 min | Halt release or roll back |
| High | P95 latency above 500 ms | 10 min | Inspect dependency latency |
| High | Pod restart count increases by 3 | 10 min | Inspect logs and probes |
| Warning | CPU above 80% | 10 min | Review HPA and traffic |
| Warning | Memory above 85% | 10 min | Check limits and leak signals |

## Evidence to capture

- AOM cluster overview
- workload replica health
- pod CPU and memory panels
- custom request/error/latency metrics
- one triggered test alarm
- incident timeline and recovery evidence

Do not include account IDs, public endpoints, tokens, or sensitive resource
identifiers in public screenshots.

