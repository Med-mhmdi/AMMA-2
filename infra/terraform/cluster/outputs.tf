output "created_namespaces" {
  value = ["amma", "kafka", "observability", "ingress-system"]
}

output "created_service_accounts" {
  value = [
    "amma/amma-gateway-sa",
    "amma/amma-microservice-sa",
    "kafka/kafka-sa"
  ]
}

output "created_secrets" {
  value = ["amma/amma-app-secrets"]
}

output "created_configmaps" {
  value = ["amma/amma-app-config"]
}
