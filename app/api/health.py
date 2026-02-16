"""
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/")
async def root():
    """
    Root endpoint - Basic health check
    """
    return {
        "status": "healthy",
        "service": "EduVerse AI",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/health")
async def health_check():
    """
    Detailed health check endpoint
    """
    return {
        "status": "healthy",
        "service": "EduVerse AI",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "operational",
            "database": "not_configured",
            "vector_store": "not_configured",
            "llm": "not_configured"
        }
    }
