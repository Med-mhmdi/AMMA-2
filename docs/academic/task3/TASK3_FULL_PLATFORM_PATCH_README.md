# AMMA Full Task 3 Platform Patch

Copy this patch into AMMA-2 root.

## What it adds
- k3d + Cilium setup script.
- Terraform cluster base resources.
- Helm charts for 7 AMMA microservices.
- ArgoCD App of Apps manifests.
- Ansible Strimzi Kafka role.
- Istio mesh policies: retries, circuit breaker, rate limiting.
- HAProxy/Keepalived ingress manifests.
- Kubernetes observability values/manifests.
- GitHub Actions self-hosted runner workflow using Kaniko.
- Locust platform load test.
- Defense docs and requirement matrix.

## Apply
```powershell
Copy-Item -Recurse -Force AMMA_TASK3_FULL_PLATFORM_PATCH\* AMMA-2\
```

Then follow:
`docs/platform/IMPLEMENTATION_ORDER.md`
