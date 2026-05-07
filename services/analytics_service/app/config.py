import os


class Settings:
    APP_NAME: str = "AMMA Analytics Service"
    APP_ENV: str = os.getenv("APP_ENV", "development")

    EXPENSE_SERVICE_URL: str = os.getenv(
        "EXPENSE_SERVICE_URL",
        "http://expense_service:8000",
    )
    LOAN_SERVICE_URL: str = os.getenv(
        "LOAN_SERVICE_URL",
        "http://loan_service:8000",
    )
    REDIS_URL: str = os.getenv(
        "REDIS_URL",
        "redis://redis:6379/0",
    )

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change_me_super_secret_key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")


settings = Settings()