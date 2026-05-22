# Creates local k3s-based Kubernetes cluster with Cilium CNI.
# Requirements: Docker Desktop, kubectl, helm, k3d, cilium CLI.

$ErrorActionPreference = "Stop"

$clusterName = "amma-platform"

Write-Host "Deleting old cluster if exists..."
k3d cluster delete $clusterName 2>$null

Write-Host "Creating k3d cluster without default flannel..."
k3d cluster create $clusterName `
  --agents 2 `
  --servers 1 `
  --api-port 6550 `
  --port "8080:80@loadbalancer" `
  --port "8443:443@loadbalancer" `
  --k3s-arg "--flannel-backend=none@server:*" `
  --k3s-arg "--disable-network-policy@server:*" `
  --k3s-arg "--disable=traefik@server:*" `
  --wait

kubectl cluster-info

Write-Host "Installing Cilium..."
helm repo add cilium https://helm.cilium.io/
helm repo update

helm upgrade --install cilium cilium/cilium `
  --namespace kube-system `
  --set kubeProxyReplacement=false `
  --set k8sServiceHost=host.k3d.internal `
  --set k8sServicePort=6550 `
  --set hubble.relay.enabled=true `
  --set hubble.ui.enabled=true `
  --set operator.replicas=1

Write-Host "Waiting for Cilium..."
kubectl -n kube-system rollout status ds/cilium --timeout=300s
kubectl -n kube-system rollout status deployment/cilium-operator --timeout=300s

Write-Host "Cluster is ready."
kubectl get nodes -o wide
kubectl get pods -n kube-system
