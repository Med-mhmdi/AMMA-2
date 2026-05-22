$ErrorActionPreference = "Stop"

$registryName = "amma-registry"
$registryPort = "5000"

docker ps -a --format "{{.Names}}" | Select-String "^$registryName$" | ForEach-Object {
  docker rm -f $registryName
}

docker run -d -p ${registryPort}:5000 --restart=always --name $registryName registry:2

Write-Host "Local registry started: localhost:5000"
curl http://localhost:5000/v2/
