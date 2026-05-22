# AMMA Full Task 3 Implementation Order

Use this order. Do not jump randomly.

## Phase 0 - Keep Docker proof
Keep your current Docker Compose screenshots. They prove the application works before Kubernetes migration.

## Phase 1 - Kubernetes cluster with Cilium
Run:
```powershell
scripts/task3/01_create_k3d_cilium.ps1
```

Verify:
```powershell
kubectl get nodes -o wide
cilium status
kubectl get pods -A
```

## Phase 2 - Terraform base resources
Run:
```powershell
cd infra/terraform/cluster
terraform init
terraform plan
terraform apply -auto-approve
cd ../../..
```

Verify:
```powershell
kubectl get ns
kubectl get sa -n amma
kubectl get secret -n amma
```

## Phase 3 - Local registry and images
Run:
```powershell
scripts/task3/02_start_local_registry.ps1
scripts/task3/03_build_push_images.ps1
```

Verify:
```powershell
curl http://localhost:5000/v2/_catalog
```

## Phase 4 - Kafka with Ansible + Strimzi
Run:
```powershell
ansible-galaxy collection install kubernetes.core
ansible-playbook infra/ansible/playbooks/deploy-kafka.yml
```

Verify:
```powershell
kubectl get pods -n kafka
kubectl get kafka -n kafka
```

## Phase 5 - ArgoCD App of Apps
Run:
```powershell
scripts/task3/04_install_argocd.ps1
kubectl apply -f infra/argocd/projects/amma-platform-project.yaml
kubectl apply -f infra/argocd/app-of-apps/root-application.yaml
```

Verify:
```powershell
kubectl get applications -n argocd
```

## Phase 6 - Helm deploy 3+ services
Either let ArgoCD sync or deploy manually:
```powershell
helm upgrade --install amma-gateway infra/helm/amma-gateway -n amma
helm upgrade --install amma-auth infra/helm/amma-auth-service -n amma
helm upgrade --install amma-expense infra/helm/amma-expense-service -n amma
```

Verify:
```powershell
kubectl get deploy,svc,pod -n amma
```

## Phase 7 - Istio mesh, retries, circuit breaker, rate limit
Run:
```powershell
scripts/task3/05_install_istio.ps1
kubectl apply -f infra/istio/
kubectl apply -f infra/istio/ratelimit/
```

Verify:
```powershell
kubectl get pods -n istio-system
kubectl get destinationrule,virtualservice,envoyfilter -n amma
```

## Phase 8 - Ingress
For local demo, use Istio ingress gateway or HAProxy/MetalLB.
```powershell
kubectl apply -f infra/ingress/haproxy/
```

## Phase 9 - Observability in Kubernetes
Your Docker observability is already working. For K8s:
```powershell
kubectl apply -f infra/observability/k8s/
```
or install via Helm values from `infra/observability/k8s/helm-values`.

## Phase 10 - Load and failure tests
Run:
```powershell
locust -f tests/load/locust_platform.py --host=http://localhost
scripts/task3/07_circuit_breaker_test.ps1
```

