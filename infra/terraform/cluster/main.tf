resource "terraform_data" "amma_base_infrastructure" {
  input = "amma-task3-base-infra"

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]

    command = <<EOT
kubectl create namespace amma --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace kafka --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace observability --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace ingress-system --dry-run=client -o yaml | kubectl apply -f -

kubectl create serviceaccount amma-gateway-sa -n amma --dry-run=client -o yaml | kubectl apply -f -
kubectl create serviceaccount amma-service-sa -n amma --dry-run=client -o yaml | kubectl apply -f -
kubectl create serviceaccount kafka-sa -n kafka --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic amma-app-secrets -n amma --from-literal=JWT_SECRET_KEY=dev-secret --from-literal=POSTGRES_PASSWORD=postgres --from-literal=REDIS_PASSWORD=redis --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic amma-minio-secrets -n amma --from-literal=MINIO_ROOT_USER=minio --from-literal=MINIO_ROOT_PASSWORD=minio123 --dry-run=client -o yaml | kubectl apply -f -

kubectl create configmap amma-platform-config -n amma --from-literal=APP_ENV=development --from-literal=KAFKA_BOOTSTRAP_SERVERS=amma-kafka-kafka-bootstrap.kafka.svc.cluster.local:9092 --from-literal=REDIS_URL=redis://redis.amma.svc.cluster.local:6379 --from-literal=MONGO_URL=mongodb://mongodb.amma.svc.cluster.local:27017 --dry-run=client -o yaml | kubectl apply -f -
EOT
  }
}
