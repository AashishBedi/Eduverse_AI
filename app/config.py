"""
Configuration management for EduVerse AI
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application settings with environment variable support
    """

    # Application
    APP_NAME: str = "EduVerse AI"
    DEBUG: bool = True

    # CORS — stored as a plain string, split at runtime in main.py
    # In .env, set as:  ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"

    def get_allowed_origins(self) -> List[str]:
        """Return ALLOWED_ORIGINS as a list, splitting on commas."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # Database
    DATABASE_URL: str = "sqlite:///./eduverse.db"

    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    RESET_TOKEN_EXPIRE_MINUTES: int = 15

    # Default admin credentials (first-startup seed)
    ADMIN_DEFAULT_EMAIL: str = "admin@eduverse.edu"
    ADMIN_DEFAULT_PASSWORD: str = "Admin@1234"

    # AI/LLM Configuration
    EMBEDDING_MODEL: str = "BAAI/bge-base-en-v1.5"
    EMBEDDING_MODEL_ALT: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Ollama Configuration (legacy — not used, kept for compat)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3"
    OLLAMA_MODEL_ALT: str = "llama2"
    OLLAMA_TIMEOUT: int = 120

    # Groq API Configuration (active LLM)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-8b-8192"

    # Vector Store Configuration
    VECTOR_STORE_PATH: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "eduverse_documents"

    # RAG Configuration
    RAG_TOP_K: int = 3
    RAG_MAX_CONTEXT_LENGTH: int = 2000
    RAG_SIMILARITY_THRESHOLD: float = 0.5
    RAG_MIN_CONFIDENCE: float = 0.3

    # Evaluation Configuration
    ENABLE_EVALUATION_LOGGING: bool = True
    EVALUATION_LOG_PATH: str = "./data/evaluation_logs"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
