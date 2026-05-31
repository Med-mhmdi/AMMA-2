resource "terraform_data" "amma_base_infrastructure" {
  input = "amma-task3-base-infra-v2"

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]

    command = <<EOT
kubectl create namespace amma --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace kafka --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace observability --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace ingress-system --dry-run=client -o yaml | kubectl apply -f -

kubectl create serviceaccount amma-gateway-sa -n amma --dry-run=client -o yaml | kubectl apply -f -
kubectl create serviceaccount amma-microservice-sa -n amma --dry-run=client -o yaml | kubectl apply -f -
kubectl create serviceaccount kafka-sa -n kafka --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic amma-app-secrets -n amma --from-literal=JWT_SECRET_KEY=dev-secret --from-literal=POSTGRES_PASSWORD=postgres --from-literal=REDIS_PASSWORD=redis --from-literal=MINIO_ROOT_USER=minio --from-literal=MINIO_ROOT_PASSWORD=minio123 --dry-run=client -o yaml | kubectl apply -f -

kubectl create configmap amma-app-config -n amma --from-literal=APP_ENV=development --from-literal=APP_DEBUG=true --from-literal=AUTH_SERVICE_URL=http://amma-auth-service.amma.svc.cluster.local:8000 --from-literal=EXPENSE_SERVICE_URL=http://amma-expense-service.amma.svc.cluster.local:8000 --from-literal=LOAN_SERVICE_URL=http://amma-loan-service.amma.svc.cluster.local:8000 --from-literal=ANALYTICS_SERVICE_URL=http://amma-analytics-service.amma.svc.cluster.local:8000 --from-literal=NOTIFICATION_SERVICE_URL=http://amma-notification-service.amma.svc.cluster.local:8000 --from-literal=AGENT_SERVICE_URL=http://amma-agent-service.amma.svc.cluster.local:8000 --from-literal=AUTH_DATABASE_URL=postgresql+psycopg2://postgres:postgres@amma-postgres.amma.svc.cluster.local:5432/amma_db --from-literal=EXPENSE_DATABASE_URL=postgresql+psycopg2://postgres:postgres@amma-postgres.amma.svc.cluster.local:5432/amma_db --from-literal=LOAN_DATABASE_URL=postgresql+psycopg2://postgres:postgres@amma-postgres.amma.svc.cluster.local:5432/amma_db --from-literal=NOTIFICATION_DATABASE_URL=postgresql+psycopg2://postgres:postgres@amma-postgres.amma.svc.cluster.local:5432/amma_db --from-literal=REDIS_URL=redis://amma-redis.amma.svc.cluster.local:6379 --from-literal=MONGODB_URL=mongodb://amma-mongodb.amma.svc.cluster.local:27017 --from-literal=MONGODB_DB_NAME=agent_memory_db --from-literal=KAFKA_BOOTSTRAP_SERVERS=amma-kafka-bootstrap.kafka.svc.cluster.local:9092 --dry-run=client -o yaml | kubectl apply -f -
EOT
  }
}
