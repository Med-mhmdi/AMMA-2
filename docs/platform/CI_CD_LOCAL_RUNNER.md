# Local CI/CD Runner Setup

Use a GitHub Actions self-hosted runner or GitLab Runner on your PC.

## Why local runner?
The assignment asks for local image build pipeline. A local runner can access:
- local Docker/k3d cluster
- local registry `localhost:5000`
- ArgoCD CLI

## Pipeline logic
1. Checkout code.
2. Build image using Kaniko.
3. Push image to local registry.
4. Update Helm chart image tag.
5. Commit/push chart change.
6. ArgoCD detects change and syncs.

## Evidence screenshots
- Runner online.
- Pipeline run successful.
- Local registry catalog contains images.
- ArgoCD application synced.
