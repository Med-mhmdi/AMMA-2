param(
    [string]$IstioVersion = "1.29.3"
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " AMMA Task 3 - Safe Istio Installation" -ForegroundColor Cyan
Write-Host " Target Istio version: $IstioVersion" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

function Run-Step {
    param(
        [string]$Title,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host ">>> $Title" -ForegroundColor Yellow
    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Title"
    }
}

Run-Step "Checking kubectl access" {
    kubectl get nodes
}

Run-Step "Checking AMMA namespace" {
    kubectl get namespace amma
}

Write-Host ""
Write-Host "Kubernetes version:" -ForegroundColor Yellow
kubectl version
if ($LASTEXITCODE -ne 0) {
    kubectl version
}

Write-Host ""
Write-Host "Installing Istio using lightweight demo profile..." -ForegroundColor Yellow
Write-Host "This script intentionally avoids the heavy full profile and egress gateway." -ForegroundColor DarkYellow

Run-Step "Uninstalling any previous broken Istio installation" {
    istioctl uninstall --purge -y
}

kubectl delete namespace istio-system --ignore-not-found=true | Out-Null

Write-Host ""
Write-Host "Waiting for old istio-system namespace to disappear if it exists..." -ForegroundColor Yellow
for ($i = 0; $i -lt 30; $i++) {
    $ns = kubectl get ns istio-system --ignore-not-found 2>$null
    if ([string]::IsNullOrWhiteSpace($ns)) {
        break
    }
    Start-Sleep -Seconds 2
}

Run-Step "Installing Istio demo profile with reduced gateways" {
    istioctl install `
        --set profile=demo `
        --set tag=$IstioVersion `
        --set components.egressGateways[0].enabled=false `
        --set values.gateways.istio-ingressgateway.autoscaleEnabled=false `
        --set values.gateways.istio-ingressgateway.resources.requests.cpu=50m `
        --set values.gateways.istio-ingressgateway.resources.requests.memory=64Mi `
        --set values.gateways.istio-ingressgateway.resources.limits.cpu=500m `
        --set values.gateways.istio-ingressgateway.resources.limits.memory=512Mi `
        -y
}

Run-Step "Labeling AMMA namespace for sidecar injection" {
    kubectl label namespace amma istio-injection=enabled --overwrite
}

Write-Host ""
Write-Host "Waiting for Istio pods..." -ForegroundColor Yellow
kubectl rollout status deployment/istiod -n istio-system --timeout=300s
kubectl rollout status deployment/istio-ingressgateway -n istio-system --timeout=300s

Write-Host ""
Write-Host "Creating AMMA Istio Gateway and VirtualService..." -ForegroundColor Yellow

@"
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: amma-gateway
  namespace: amma
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 80
        name: http
        protocol: HTTP
      hosts:
        - "*"
---
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: amma-gateway-vs
  namespace: amma
spec:
  hosts:
    - "*"
  gateways:
    - amma-gateway
  http:
    - match:
        - uri:
            prefix: /
      route:
        - destination:
            host: amma-gateway.amma.svc.cluster.local
            port:
              number: 8000
"@ | Set-Content amma-istio-routing.yaml

Run-Step "Applying Istio routing resources" {
    kubectl apply -f amma-istio-routing.yaml
}

Write-Host ""
Write-Host "Restarting AMMA deployments to inject Istio sidecars..." -ForegroundColor Yellow
kubectl rollout restart deployment -n amma

Write-Host ""
Write-Host "Waiting for AMMA gateway rollout..." -ForegroundColor Yellow
kubectl rollout status deployment/amma-gateway -n amma --timeout=300s

Write-Host ""
Write-Host "Final Istio status:" -ForegroundColor Green
kubectl get pods -n istio-system
kubectl get gateway -A
kubectl get virtualservice -A
kubectl get pods -n amma

Write-Host ""
Write-Host "Istio installation finished successfully." -ForegroundColor Green
Write-Host "To test ingress, run:" -ForegroundColor Cyan
Write-Host "kubectl port-forward svc/istio-ingressgateway -n istio-system 8089:80" -ForegroundColor Cyan
Write-Host "Then in another PowerShell:" -ForegroundColor Cyan
Write-Host "Invoke-WebRequest -UseBasicParsing http://localhost:8089/health" -ForegroundColor Cyan
