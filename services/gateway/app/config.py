import os


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "AMMA API Gateway")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_DEBUG: str = os.getenv("APP_DEBUG", "true")

    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000")
    EXPENSE_SERVICE_URL: str = os.getenv("EXPENSE_SERVICE_URL", "http://expense_service:8000")
    LOAN_SERVICE_URL: str = os.getenv("LOAN_SERVICE_URL", "http://loan_service:8000")
    ANALYTICS_SERVICE_URL: str = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics_service:8000")
    NOTIFICATION_SERVICE_URL: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification_service:8000")
    AGENT_SERVICE_URL: str = os.getenv("AGENT_SERVICE_URL", "http://multi_agent_system:8000")

    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ROOT_USER: str = os.getenv("MINIO_ROOT_USER", "minio")
    MINIO_ROOT_PASSWORD: str = os.getenv("MINIO_ROOT_PASSWORD", "minio123")
    MINIO_SECURE: str = os.getenv("MINIO_SECURE", "false")


settings = Settings()
