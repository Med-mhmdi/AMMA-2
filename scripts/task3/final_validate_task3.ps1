Write-Host "================ AMMA TASK 3 FINAL VALIDATION ================"

Write-Host "`n[1] Kubernetes nodes"
kubectl get nodes -o wide

Write-Host "`n[2] Cilium status"
cilium status

Write-Host "`n[3] Terraform-created namespaces/config"
kubectl get ns
kubectl get serviceaccount -n amma
kubectl get secret -n amma
kubectl get configmap -n amma

Write-Host "`n[4] ArgoCD applications"
kubectl get applications -n argocd

Write-Host "`n[5] Kafka on Kubernetes"
kubectl get pods -n kafka
kubectl get svc -n kafka
kubectl exec -n kafka amma-kafka-0 -- kafka-topics --bootstrap-server amma-kafka.kafka.svc.cluster.local:9092 --list

Write-Host "`n[6] AMMA Helm deployments"
kubectl get deploy -n amma
kubectl get pods -n amma
kubectl get svc -n amma
kubectl get hpa -n amma

Write-Host "`n[7] Istio service mesh"
kubectl get pods -n istio-system
kubectl get gateway -n amma
kubectl get virtualservice -n amma
kubectl get destinationrule -n amma
kubectl get envoyfilter -A

Write-Host "`n[8] Gateway through Istio ingress"
Write-Host "Run this in another terminal if port-forward is not active:"
Write-Host "kubectl port-forward svc/istio-ingressgateway -n istio-system 8089:80"
try {
  Invoke-WebRequest -Uri "http://localhost:8089/health" -UseBasicParsing
} catch {
  Write-Host "Istio ingress test skipped or port-forward not running."
}

Write-Host "`n[9] Rate limit quick test"
1..10 | ForEach-Object {
  try {
    $r = Invoke-WebRequest -Uri "http://localhost:8089/health" -UseBasicParsing
    "$_ -> $($r.StatusCode)"
  } catch {
    "$_ -> $($_.Exception.Response.StatusCode.value__)"
  }
}

Write-Host "`n[10] Locust file"
Get-Item tests\load\locust_platform.py

Write-Host "`n================ VALIDATION DONE ================"
