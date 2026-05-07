import os


class Settings:
    APP_NAME: str = "AMMA API Gateway"

    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000")
    EXPENSE_SERVICE_URL: str = os.getenv("EXPENSE_SERVICE_URL", "http://expense_service:8000")
    LOAN_SERVICE_URL: str = os.getenv("LOAN_SERVICE_URL", "http://loan_service:8000")
    ANALYTICS_SERVICE_URL: str = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics_service:8000")
    NOTIFICATION_SERVICE_URL: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification_service:8000")

settings = Settings()