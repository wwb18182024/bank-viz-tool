"""Application configuration. All values overridable via environment variables."""
import os


class Settings:
    APP_NAME: str = "BankViz API"
    # Privacy: the LLM endpoint MUST be local. Remote endpoints are refused (fail closed).
    OLLAMA_URL: str = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_K_M")
    MAX_UPLOAD_MB: int = int(os.environ.get("MAX_UPLOAD_MB", "100"))
    TOP_K_CATEGORIES: int = int(os.environ.get("TOP_K_CATEGORIES", "10"))
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    ALLOWED_EXTENSIONS: set = {".csv", ".xlsx", ".xls"}


settings = Settings()
