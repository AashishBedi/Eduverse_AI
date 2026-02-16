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
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # Database
    DATABASE_URL: str = "sqlite:///./eduverse.db"
    
    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI/LLM Configuration
    # AI/LLM Configuration
    EMBEDDING_MODEL: str = "BAAI/bge-base-en-v1.5"
    EMBEDDING_MODEL_ALT: str = "sentence-transformers/all-MiniLM-L6-v2"  # Alternative for comparison
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3"
    OLLAMA_MODEL_ALT: str = "llama2"  # Alternative LLM for comparison
    OLLAMA_TIMEOUT: int = 120
    
    # Vector Store Configuration
    VECTOR_STORE_PATH: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "eduverse_documents"
    
    # RAG Configuration
    RAG_TOP_K: int = 3
    RAG_MAX_CONTEXT_LENGTH: int = 2000
    RAG_SIMILARITY_THRESHOLD: float = 0.5  # Minimum similarity score for retrieval
    RAG_MIN_CONFIDENCE: float = 0.3  # Absolute minimum for any response
    
    # Evaluation Configuration
    ENABLE_EVALUATION_LOGGING: bool = True
    EVALUATION_LOG_PATH: str = "./data/evaluation_logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
