resource "kubernetes_namespace" "amma" {
  metadata {
    name = var.namespace
    labels = {
      "istio-injection" = "enabled"
      "project"         = "amma"
    }
  }
}

resource "kubernetes_namespace" "kafka" {
  metadata {
    name = "kafka"
  }
}

resource "kubernetes_service_account" "gateway" {
  metadata {
    name      = "amma-gateway-sa"
    namespace = kubernetes_namespace.amma.metadata[0].name
  }
}

resource "kubernetes_service_account" "microservice" {
  metadata {
    name      = "amma-microservice-sa"
    namespace = kubernetes_namespace.amma.metadata[0].name
  }
}

resource "kubernetes_secret" "app_secrets" {
  metadata {
    name      = "amma-app-secrets"
    namespace = kubernetes_namespace.amma.metadata[0].name
  }

  data = {
    JWT_SECRET_KEY       = "change-me-local"
    POSTGRES_PASSWORD    = "postgres"
    MINIO_ROOT_USER      = "minio"
    MINIO_ROOT_PASSWORD  = "minio123"
  }

  type = "Opaque"
}

resource "kubernetes_config_map" "app_config" {
  metadata {
    name      = "amma-app-config"
    namespace = kubernetes_namespace.amma.metadata[0].name
  }

  data = {
    APP_ENV                  = "development"
    KAFKA_BOOTSTRAP_SERVERS  = "amma-kafka-bootstrap.kafka:9092"
    REDIS_HOST               = "redis"
    MONGODB_URL              = "mongodb://mongodb:27017"
    MINIO_ENDPOINT           = "minio:9000"
    AUTH_SERVICE_URL         = "http://amma-auth-service:8000"
    EXPENSE_SERVICE_URL      = "http://amma-expense-service:8000"
    LOAN_SERVICE_URL         = "http://amma-loan-service:8000"
    ANALYTICS_SERVICE_URL    = "http://amma-analytics-service:8000"
    NOTIFICATION_SERVICE_URL = "http://amma-notification-service:8000"
    AGENT_SERVICE_URL        = "http://amma-agent-service:8000"
  }
}
