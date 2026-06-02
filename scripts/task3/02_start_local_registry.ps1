$ErrorActionPreference = "Stop"

$registryName = "amma-registry.localhost"
$registryContainer = "k3d-$registryName"
$registryPort = "5000"

$existingRegistry = docker ps -a --format "{{.Names}}" | Select-String "^$([regex]::Escape($registryContainer))$"

if (-not $existingRegistry) {
  k3d registry create $registryName --port "0.0.0.0:$registryPort"
}

Write-Host "Local k3d registry available from host: http://localhost:$registryPort"
Write-Host "Local k3d registry available from k3d nodes: http://${registryContainer}:5000"
curl http://localhost:$registryPort/v2/
