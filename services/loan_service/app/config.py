import os


class Settings:
    APP_NAME: str = "AMMA Loan Service"
    APP_ENV: str = os.getenv("APP_ENV", "development")

    DATABASE_URL: str = os.getenv(
        "LOAN_DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@loan_db:5432/loan_db",
    )

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change_me_super_secret_key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")


settings = Settings()