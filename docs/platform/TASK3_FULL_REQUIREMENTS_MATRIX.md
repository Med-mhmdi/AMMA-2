# AMMA Task 3 Full Platform Requirements Matrix

This document maps the teacher requirements to AMMA deliverables.

## Current AMMA base already working in Docker Compose
- Microservices: gateway, auth, expense, loan, analytics, notification, multi_agent_system.
- Data: PostgreSQL per service, MongoDB, Redis, MinIO.
- Messaging: Kafka topics and event flow.
- Routing: Nginx Gateway.
- Observability: Prometheus `/metrics`, Grafana dashboard, Loki + Promtail logs, Jaeger UI, LangSmith AI traces.
- Storage: Gateway endpoints store receipts, reports, and analytics snapshots in MinIO.

## Full platform layer required by the new assignment
| Unit | Requirement | Deliverable added by this patch | Verification |
|---|---|---|---|
| 1.1 | Local Kubernetes cluster k3s/k0s/Talos + Cilium | `scripts/task3/01_create_k3d_cilium.ps1` | `kubectl get nodes`, `cilium status` |
| 1.2 | Karpenter / Cluster Autoscaler | `infra/k8s/platform/autoscaling/hpa.yaml`, notes for CA limitation | `kubectl get hpa -n amma` |
| 2.1 | Terraform namespaces, service accounts, secrets | `infra/terraform/cluster/*` | `terraform apply`, `kubectl get ns,sa,secret -n amma` |
| 2.2 | ArgoCD App of Apps | `infra/argocd/*` | ArgoCD UI shows synced applications |
| 2.3 | Ansible Role for Kafka/Strimzi | `infra/ansible/roles/strimzi_kafka/*` | `ansible-playbook infra/ansible/playbooks/deploy-kafka.yml` |
| 3.1 | Istio/Linkerd service mesh + circuit breaker/retries | `infra/istio/*` | `kubectl get destinationrule,virtualservice -n amma` |
| 3.2 | Ingress Controller + HAProxy/Keepalived | `infra/ingress/haproxy/*`, `infra/ingress/keepalived/*` | HAProxy/MetalLB/Keepalived manifests applied |
| 3.3 | Gateway/API rate limiting | `infra/istio/ratelimit/envoyfilter-local-rate-limit.yaml` | send many requests and observe 429 |
| 4 | Observability | `infra/observability/k8s/*` + existing Docker observability | Grafana, Prometheus, Loki, Jaeger screenshots |
| 5.1 | Local CI runner | `.github/workflows/build-kaniko-argocd.yml`, `docs/platform/CI_CD_LOCAL_RUNNER.md` | self-hosted runner online |
| 5.2 | Kaniko build, push local registry, update Helm, ArgoCD sync | workflow + `infra/registry/local-registry.yaml` | images pushed, Helm values updated |
| 5.3 | Helm charts for 3+ microservices | `infra/helm/amma-*` | `helm upgrade --install ...` |
| 6.1 | Locust load test through gateway generating Kafka events | `tests/load/locust_platform.py` | Locust UI + Kafka logs/events |
| 6.2 | Circuit breaker verification | `scripts/task3/07_circuit_breaker_test.ps1` | requests fail fast / outlier detection evidence |
| 6.3 | Grafana dashboards for Kafka latency/queue/rate limiter | `infra/observability/k8s/grafana-dashboards/*` | dashboard panels visible |

## Important honest note
Karpenter is cloud-provider oriented. On a local k3d/k3s cluster, true automatic creation of new worker nodes is not realistic without Cluster API or a cloud provider. For local defense, use:
1. HPA for pod autoscaling under load.
2. Optional Cluster Autoscaler manifest documented as cloud/Cluster API extension.
3. Explain the limitation honestly.

