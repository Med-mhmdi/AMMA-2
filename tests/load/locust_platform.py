from locust import HttpUser, task, between
import random
import time

class AmmaPlatformUser(HttpUser):
    wait_time = between(0.2, 1.0)

    @task(5)
    def health_gateway(self):
        self.client.get("/health", name="gateway health")

    @task(2)
    def auth_health(self):
        self.client.get("/auth/health", name="auth health")

    @task(2)
    def expense_health(self):
        self.client.get("/expenses/health", name="expense health")

    @task(1)
    def analytics_health(self):
        self.client.get("/analytics/health", name="analytics health")

    @task(1)
    def simulate_expense_payload(self):
        payload = {
            "description": "Locust test expense",
            "amount": random.randint(10, 500),
            "category_id": 1,
            "type": "outcome",
            "transaction_date": "2026-05-22"
        }
        self.client.post("/expenses", json=payload, name="create expense")
