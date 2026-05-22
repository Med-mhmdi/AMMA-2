kubectl create namespace observability --dry-run=client -o yaml | kubectl apply -f -

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack `
  -n observability `
  -f infra/observability/k8s/helm-values/kube-prometheus-stack-values.yaml

helm upgrade --install loki grafana/loki `
  -n observability `
  -f infra/observability/k8s/helm-values/loki-values.yaml

helm upgrade --install promtail grafana/promtail `
  -n observability `
  -f infra/observability/k8s/helm-values/promtail-values.yaml

kubectl apply -f infra/observability/k8s/otel-collector.yaml
