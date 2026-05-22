output "amma_namespace" {
  value = kubernetes_namespace.amma.metadata[0].name
}

output "kafka_namespace" {
  value = kubernetes_namespace.kafka.metadata[0].name
}
