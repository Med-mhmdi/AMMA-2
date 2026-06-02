$ErrorActionPreference = "Stop"

$namespace = "argocd"
$releaseName = "argocd"

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

function Test-NamespaceExists {
  param([string]$Name)

  $result = kubectl get namespace $Name --ignore-not-found
  return -not [string]::IsNullOrWhiteSpace($result)
}

function Test-HelmReleaseExists {
  param(
    [string]$Name,
    [string]$Namespace
  )

  $result = helm list -n $Namespace -q | Select-String "^$([regex]::Escape($Name))$"
  return $null -ne $result
}

function Test-KubernetesResourceExists {
  param(
    [string]$Resource,
    [string]$Name,
    [string]$Namespace
  )

  $result = kubectl get $Resource $Name -n $Namespace --ignore-not-found
  return -not [string]::IsNullOrWhiteSpace($result)
}

$namespaceExists = Test-NamespaceExists $namespace
$helmReleaseExists = $false
$rawInstallExists = $false

if ($namespaceExists) {
  $helmReleaseExists = Test-HelmReleaseExists $releaseName $namespace
  $rawInstallExists = Test-KubernetesResourceExists "deployment" "argocd-server" $namespace
}

if ($namespaceExists -and -not $helmReleaseExists -and $rawInstallExists) {
  Run-Step "Removing existing non-Helm Argo CD namespace" {
    kubectl delete namespace $namespace --wait=true
  }
}

Run-Step "Creating argocd namespace" {
  kubectl create namespace $namespace --dry-run=client -o yaml | kubectl apply -f -
}

Run-Step "Adding Argo Helm repository" {
  helm repo add argo https://argoproj.github.io/argo-helm --force-update
}

Run-Step "Updating Helm repositories" {
  helm repo update
}

if (-not (Test-KubernetesResourceExists "secret" "argocd-redis" $namespace)) {
  $redisPassword = [guid]::NewGuid().ToString("N")

  Run-Step "Creating argocd-redis secret" {
    kubectl create secret generic argocd-redis -n $namespace --from-literal=auth=$redisPassword --dry-run=client -o yaml | kubectl apply -f -
  }
}

Run-Step "Installing Argo CD with Helm" {
  helm upgrade --install $releaseName argo/argo-cd `
    -n $namespace `
    --set redis.enabled=true `
    --set redis-ha.enabled=false `
    --set redisSecretInit.enabled=false
}

Run-Step "Waiting for argocd-redis" {
  kubectl -n $namespace rollout status deployment/argocd-redis --timeout=600s
}

Run-Step "Waiting for argocd-repo-server" {
  kubectl -n $namespace rollout status deployment/argocd-repo-server --timeout=600s
}

Run-Step "Waiting for argocd-application-controller" {
  kubectl -n $namespace rollout status statefulset/argocd-application-controller --timeout=600s
}

Run-Step "Waiting for argocd-server" {
  kubectl -n $namespace rollout status deployment/argocd-server --timeout=600s
}

Run-Step "Waiting for argocd-dex-server" {
  kubectl -n $namespace rollout status deployment/argocd-dex-server --timeout=600s
}

Run-Step "Waiting for argocd-applicationset-controller" {
  kubectl -n $namespace rollout status deployment/argocd-applicationset-controller --timeout=600s
}

Write-Host ""
Write-Host "Argo CD installed." -ForegroundColor Green
Write-Host "Port-forward command:"
Write-Host "kubectl port-forward svc/argocd-server -n argocd 8081:443"

if (Test-KubernetesResourceExists "secret" "argocd-initial-admin-secret" $namespace) {
  Write-Host "Initial admin password:"
  kubectl -n $namespace get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
} else {
  Write-Host "Initial admin password secret was not found." -ForegroundColor Yellow
}
