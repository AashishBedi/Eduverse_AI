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
    allow_origins=settings.get_allowed_origins(),
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
    print("🚀 EduVerse AI Backend starting up...")

    # 1. Init database tables
    try:
        from app.db.init_db import init_database
        init_database()
    except Exception as e:
        print(f"⚠️  Database init warning: {e}")

    # 2. Seed default admin (non-fatal — server still starts if this fails)
    try:
        from app.db.database import SessionLocal
        from app.services.auth_service import get_or_create_default_admin
        with SessionLocal() as db:
            get_or_create_default_admin(db)
    except Exception as e:
        print(f"⚠️  Admin seed warning: {e}")
        print("   → Server is running. Log in manually or check ADMIN_DEFAULT_PASSWORD in .env")

    print("✅ EduVerse AI is ready → http://127.0.0.1:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 EduVerse AI Backend shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

