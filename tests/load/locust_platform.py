from locust import HttpUser, task, between
import random
import string
from datetime import date


def random_email():
    token = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"load_{token}@amma.test"


class AmmaPlatformUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self):
        self.token = None
        self.email = random_email()
        password = "Password123!"

        payload = {
            "first_name": "Load",
            "family_name": "Tester",
            "email": self.email,
            "phone_number": "1000000000",
            "password": password,
        }

        self.client.post("/auth/register", json=payload, name="/auth/register")

        login = self.client.post(
            "/auth/login",
            json={"email": self.email, "password": password},
            name="/auth/login",
        )
        try:
            data = login.json()
            self.token = data.get("access_token") or data.get("token")
        except Exception:
            self.token = None

    def headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(4)
    def create_expense_event_flow(self):
        payload = {
            "description": "locust coffee",
            "category_id": 1,
            "type": "outcome",
            "amount": random.randint(10, 300),
            "transaction_date": str(date.today()),
        }
        self.client.post("/expenses", json=payload, headers=self.headers(), name="/expenses create")

    @task(2)
    def list_expenses(self):
        self.client.get("/expenses", headers=self.headers(), name="/expenses list")

    @task(2)
    def analytics_dashboard(self):
        self.client.get("/analytics/dashboard", headers=self.headers(), name="/analytics/dashboard")

    @task(1)
    def gateway_health(self):
        self.client.get("/health", name="/health")
