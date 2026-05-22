# AMMA Task 3 Defense Script

## What AMMA demonstrates
AMMA is a microservices financial assistant platform. It includes a Gateway, Auth Service, Expense Service, Loan Service, Analytics Service, Notification Service, and AI Multi-Agent System.

## Kubernetes infrastructure
For the platform task, AMMA is deployed to a local Kubernetes cluster based on k3s using k3d. Cilium is used as the CNI to support eBPF-based networking, observability, and future network policies.

## IaC and GitOps
Terraform creates namespaces, service accounts, secrets, and config maps. ArgoCD is configured with the App of Apps pattern to synchronize AMMA services from the Git repository. Kafka deployment is automated with an Ansible role using the Strimzi operator.

## Traffic and service mesh
Istio is used as the service mesh. VirtualServices define retries and timeouts. DestinationRules implement circuit breaker behavior using connection pools and outlier detection. Gateway-level rate limiting is implemented with an Envoy local rate-limit filter.

## Observability
For AI observability, LangSmith traces the multi-agent workflow. For microservices, Prometheus scrapes `/metrics`, Grafana visualizes metrics, Promtail ships Docker/Kubernetes logs to Loki, and Jaeger is deployed for distributed tracing.

## CI/CD
A local self-hosted runner builds images with Kaniko, pushes them to a local registry, updates Helm chart image tags, and lets ArgoCD synchronize the deployment.

## Testing
Locust generates traffic through the Gateway to create expenses, call analytics, and trigger Kafka event flows. Circuit breaker behavior is validated by scaling down a service during load and observing retry/failure behavior in Grafana and Istio metrics.
