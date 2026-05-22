from locust import HttpUser, between, task


class AmmaUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.email = "loadtest@example.com"
        self.password = "password123"
        self.token = None

        # Register may fail if user already exists. That is okay for repeated tests.
        self.client.post("/register", json={
            "email": self.email,
            "password": self.password,
            "full_name": "Load Test User"
        })

        response = self.client.post("/login", json={
            "email": self.email,
            "password": self.password,
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token") or data.get("token")

    def headers(self):
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def open_dashboard(self):
        self.client.get("/analytics/dashboard", headers=self.headers())

    @task(2)
    def list_expenses(self):
        self.client.get("/expenses", headers=self.headers())

    @task(1)
    def create_expense(self):
        self.client.post("/expenses", json={
            "amount": 100,
            "description": "Locust generated expense",
            "category_id": 1,
            "type": "outcome",
            "transaction_date": "2026-05-22"
        }, headers=self.headers())

    @task(1)
    def list_loans(self):
        self.client.get("/loans", headers=self.headers())

    @task(1)
    def list_notifications(self):
        self.client.get("/notifications", headers=self.headers())
