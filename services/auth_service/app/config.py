import os


class Settings:
    APP_NAME: str = "AMMA Auth Service"
    APP_ENV: str = os.getenv("APP_ENV", "development")

    DATABASE_URL: str = os.getenv(
        "AUTH_DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@auth_db:5432/auth_db",
    )

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change_me_super_secret_key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )


settings = Settings()