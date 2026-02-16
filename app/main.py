"""
EduVerse AI - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health, auth, courses, chat, rag, timetable, upload, evaluation, admissions, fees
from app.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="EduVerse AI",
    description="AI-powered educational platform backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(rag.router, prefix="/api/rag", tags=["RAG"])
app.include_router(timetable.router, prefix="/api/timetable", tags=["Timetable"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["Evaluation"])
app.include_router(admissions.router, prefix="/api/admissions", tags=["Admissions"])
app.include_router(fees.router, prefix="/api/fees", tags=["Fees"])


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler
    Initialize connections, load models, etc.
    """
    print("🚀 EduVerse AI Backend starting up...")
    
    # Initialize database and create tables
    from app.db.init_db import init_database
    init_database()
    
    # TODO: Load AI models
    # TODO: Initialize vector store


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler
    Clean up resources
    """
    print("🛑 EduVerse AI Backend shutting down...")
    # TODO: Close database connections
    # TODO: Clean up resources


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
