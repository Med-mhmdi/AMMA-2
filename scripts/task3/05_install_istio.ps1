$ErrorActionPreference = "Stop"

# Requires istioctl installed.
istioctl install --set profile=demo -y

kubectl label namespace amma istio-injection=enabled --overwrite
kubectl -n istio-system rollout status deployment/istiod --timeout=300s
kubectl -n istio-system rollout status deployment/istio-ingressgateway --timeout=300s

Write-Host "Istio installed. Restart AMMA deployments to inject sidecars:"
kubectl rollout restart deployment -n amma
