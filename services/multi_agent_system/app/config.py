import os


class Settings:
    APP_NAME: str = "AMMA Agent Service"

    # ==========================================
    # LLM / OLLAMA
    # ==========================================

    # Ollama container URL inside Docker network
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")

    # Text model for normal agents:
    # Command Agent, Financial Advisor, Recommendation Agent, etc.
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    # Vision model for image/receipt extraction.
    # This model MUST support image input.
    # Example: llava, llama3.2-vision, qwen2.5vl if installed in Ollama.
    OLLAMA_VISION_MODEL: str = os.getenv("OLLAMA_VISION_MODEL", "llava")

    # ==========================================
    # MONGODB / AGENT MEMORY
    # ==========================================

    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "agent_memory_db")

    # ==========================================
    # INTERNAL SERVICE URLS
    # ==========================================

    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000")
    EXPENSE_SERVICE_URL: str = os.getenv("EXPENSE_SERVICE_URL", "http://expense_service:8000")
    LOAN_SERVICE_URL: str = os.getenv("LOAN_SERVICE_URL", "http://loan_service:8000")
    ANALYTICS_SERVICE_URL: str = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics_service:8000")
    NOTIFICATION_SERVICE_URL: str = os.getenv(
        "NOTIFICATION_SERVICE_URL",
        "http://notification_service:8000",
    )

    # ==========================================
    # LANGFUSE / LLM OBSERVABILITY
    # ==========================================

    # Enable/disable Langfuse tracing.
    # Keep false by default so the app can run even if Langfuse is not installed/configured.
    LANGFUSE_ENABLED: bool = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"

    # Langfuse keys from the Langfuse project settings.
    LANGFUSE_PUBLIC_KEY: str | None = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY: str | None = os.getenv("LANGFUSE_SECRET_KEY")

    # Local Langfuse default is usually http://localhost:3000 from the host machine.
    # Inside Docker network, use the service name, for example: http://langfuse-web:3000
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

    # Metadata useful for filtering traces in Langfuse.
    LANGFUSE_ENVIRONMENT: str = os.getenv("LANGFUSE_ENVIRONMENT", "development")
    LANGFUSE_RELEASE: str = os.getenv("LANGFUSE_RELEASE", "amma-multi-agent-v1")

    # Controls whether prompts/responses are sent to Langfuse.
    # For a defense/demo, true is useful. For sensitive production data, use false or mask data.
    LANGFUSE_CAPTURE_INPUT_OUTPUT: bool = (
        os.getenv("LANGFUSE_CAPTURE_INPUT_OUTPUT", "true").lower() == "true"
    )

    # Prevent very large prompts/responses from being sent to Langfuse.
    LANGFUSE_MAX_PAYLOAD_CHARS: int = int(os.getenv("LANGFUSE_MAX_PAYLOAD_CHARS", "4000"))


settings = Settings()