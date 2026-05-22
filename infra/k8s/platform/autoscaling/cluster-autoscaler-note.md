# Cluster Autoscaler note for local defense

Karpenter is designed mainly for cloud providers. Cluster Autoscaler also needs a provider that can create/delete nodes.
For local k3d/k3s, real worker-node creation is not normally automatic.

What to show locally:
- HPA scales pods under load.
- k3d can manually add nodes:
  `k3d node create amma-platform-agent-extra --cluster amma-platform`
- Explain that production Kubernetes would use Cluster Autoscaler or Karpenter with a cloud provider.

