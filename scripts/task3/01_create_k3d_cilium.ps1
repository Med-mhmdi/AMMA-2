# Creates local k3s-based Kubernetes cluster with Cilium CNI.
# Requirements: Docker Desktop, kubectl, helm, k3d, cilium CLI.

$ErrorActionPreference = "Stop"

$clusterName = "amma-platform"
$registryConfig = Join-Path $PSScriptRoot "registries.yaml"

@"
mirrors:
  "localhost:5000":
    endpoint:
      - http://k3d-amma-registry.localhost:5000
"@ | Set-Content -Encoding ASCII $registryConfig

Write-Host "Deleting old cluster if exists..."
k3d cluster delete $clusterName 2>$null

Write-Host "Creating k3d cluster without default flannel and kube-proxy..."
k3d cluster create $clusterName `
  --agents 2 `
  --servers 1 `
  --api-port 6550 `
  --port "8080:80@loadbalancer" `
  --port "8443:443@loadbalancer" `
  --registry-use k3d-amma-registry.localhost:5000 `
  --registry-config $registryConfig `
  --k3s-arg "--flannel-backend=none@server:*" `
  --k3s-arg "--disable-network-policy@server:*" `
  --k3s-arg "--disable-kube-proxy@server:*" `
  --k3s-arg "--disable=traefik@server:*" `
  --wait

kubectl cluster-info

Write-Host "Installing Cilium..."
helm repo add cilium https://helm.cilium.io/ --force-update
helm repo update

helm upgrade --install cilium cilium/cilium `
  --namespace kube-system `
  --set kubeProxyReplacement=true `
  --set k8sServiceHost=k3d-amma-platform-server-0 `
  --set k8sServicePort=6443 `
  --set bpf.masquerade=true `
  --set l7Proxy=false `
  --set envoy.enabled=false `
  --set dnsProxy.enableTransparentMode=false `
  --set proxy.useOriginalSourceAddress=false `
  --set routingMode=tunnel `
  --set tunnelProtocol=vxlan `
  --set hubble.relay.enabled=true `
  --set hubble.ui.enabled=true `
  --set operator.replicas=1

Write-Host "Waiting for Cilium..."
kubectl -n kube-system rollout status ds/cilium --timeout=300s
kubectl -n kube-system rollout status deployment/cilium-operator --timeout=300s

Write-Host "Waiting for CoreDNS..."
kubectl -n kube-system rollout status deployment/coredns --timeout=300s

Write-Host "Configuring CoreDNS external resolvers..."
$coreDnsFile = Join-Path $env:TEMP "amma-coredns-Corefile"

# Docker Desktop and k3d can expose host resolver settings that are not usable from cluster pods.
# Keep CoreDNS deterministic by forwarding external DNS directly to public resolvers.
@"
.:53 {
    errors
    health {
        lameduck 5s
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
        pods insecure
        fallthrough in-addr.arpa ip6.arpa
        ttl 30
    }
    prometheus :9153
    forward . 1.1.1.1 8.8.8.8
    cache 30
    loop
    reload
    loadbalance
}
"@ | Set-Content -Encoding ASCII $coreDnsFile

kubectl -n kube-system create configmap coredns --from-file=Corefile=$coreDnsFile --dry-run=client -o yaml | kubectl apply -f -
kubectl -n kube-system rollout restart deployment/coredns
kubectl -n kube-system rollout status deployment/coredns --timeout=300s

Write-Host "Testing Kubernetes API from inside the cluster..."
kubectl run api-test --rm -i --image=curlimages/curl --restart=Never -- curl -sk --max-time 10 https://kubernetes.default.svc/version

if ($LASTEXITCODE -ne 0) {
  throw "Pod-to-Kubernetes-API connectivity test failed. Cilium service routing is not healthy."
}

Write-Host "Cluster is ready."
kubectl get nodes -o wide
kubectl get pods -n kube-system
