from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.services.ai_service import ai_service
from app.services.memory_service import memory_service

router = APIRouter(prefix="/api/health", tags=["Health & Diagnostics"])

@router.get("", response_model=Dict[str, Any])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
    }

@router.get("/diagnostics", response_model=Dict[str, Any])
def diagnostics(db: Session = Depends(get_db)):
    # 1. Database Check
    db_ok = False
    db_error = None
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_error = str(e)

    # 2. AI Service Check
    ai_status = ai_service.check_availability()

    # 3. Hindsight Memory Check
    hindsight_status = memory_service.check_connection()

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": {
            "connected": db_ok,
            "url_type": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql",
            "error": db_error
        },
        "ai_service": {
            "provider": "Groq",
            "configured": ai_status.get("configured", False),
            "available": ai_status.get("available", False),
            "model": settings.GROQ_MODEL,
            "error": ai_status.get("error")
        },
        "memory_service": {
            "provider": "Hindsight by Vectorize",
            "base_url": settings.HINDSIGHT_BASE_URL,
            "connected": hindsight_status.get("connected", False),
            "error": hindsight_status.get("error"),
            "message": hindsight_status.get("message")
        },
        "github_integration": {
            "oauth_configured": bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET)
        }
    }
