# Circuit breaker demo:
# 1. generate traffic
# 2. break expense service
# 3. observe fast failures/retries/outlier behavior in Istio/Grafana.
param(
  [string]$Namespace = "amma"
)

Write-Host "Current pods:"
kubectl get pods -n $Namespace

Write-Host "Scaling expense service to 0 replicas..."
kubectl scale deployment amma-expense-service -n $Namespace --replicas=0

Write-Host "Generate requests now from another terminal:"
Write-Host "locust -f tests/load/locust_platform.py --host=http://localhost:8080"

Start-Sleep -Seconds 30

Write-Host "Restoring expense service..."
kubectl scale deployment amma-expense-service -n $Namespace --replicas=1
kubectl rollout status deployment/amma-expense-service -n $Namespace --timeout=180s
