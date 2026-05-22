helm repo add haproxy-ingress https://haproxy-ingress.github.io/charts
helm repo update
helm upgrade --install haproxy-ingress haproxy-ingress/haproxy-ingress `
  -n ingress-system --create-namespace `
  -f infra/ingress/haproxy/haproxy-ingress-values.yaml
