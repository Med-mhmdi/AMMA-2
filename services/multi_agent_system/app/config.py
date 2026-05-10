import os


class Settings:
    APP_NAME: str = "AMMA Agent Service"

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "agent_memory_db")

    EXPENSE_SERVICE_URL: str = os.getenv("EXPENSE_SERVICE_URL", "http://expense_service:8000")
    LOAN_SERVICE_URL: str = os.getenv("LOAN_SERVICE_URL", "http://loan_service:8000")
    ANALYTICS_SERVICE_URL: str = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics_service:8000")
    NOTIFICATION_SERVICE_URL: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification_service:8000")


settings = Settings()