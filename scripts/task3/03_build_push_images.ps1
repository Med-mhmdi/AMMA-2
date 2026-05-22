# Builds and pushes AMMA images to local registry.
$ErrorActionPreference = "Stop"

$tag = if ($env:IMAGE_TAG) { $env:IMAGE_TAG } else { "local" }
$registry = "localhost:5000"

$images = @(
  @{name="amma-gateway"; dockerfile="infra/docker/gateway.Dockerfile"},
  @{name="amma-auth-service"; dockerfile="infra/docker/auth_service.Dockerfile"},
  @{name="amma-expense-service"; dockerfile="infra/docker/expense_service.Dockerfile"},
  @{name="amma-analytics-service"; dockerfile="infra/docker/analytics_service.Dockerfile"},
  @{name="amma-notification-service"; dockerfile="infra/docker/notification_service.Dockerfile"},
  @{name="amma-loan-service"; dockerfile="infra/docker/loan_service.Dockerfile"},
  @{name="amma-multi-agent-system"; dockerfile="infra/docker/multi_agent_system.Dockerfile"}
)

foreach ($image in $images) {
  $full = "$registry/$($image.name):$tag"
  Write-Host "Building $full"
  docker build -f $image.dockerfile -t $full .
  docker push $full
}

curl http://localhost:5000/v2/_catalog
