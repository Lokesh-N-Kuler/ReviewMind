from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.feedback import ReviewFeedback
from app.schemas.memory import (
    MemoryItem,
    MemoryRetainRequest,
    MemoryRecallRequest,
    MemoryBankStatus,
    MemoryActivityLog,
)
from app.schemas.review import RecalledMemoryItem
from app.routers.auth import get_current_user
from app.services.memory_service import memory_service

router = APIRouter(prefix="/api/memory", tags=["Hindsight Memory"])

@router.get("/status", response_model=Dict[str, Any])
def get_hindsight_server_status():
    """Inspect global connectivity to the Hindsight agent memory server."""
    conn = memory_service.check_connection()
    return conn

@router.get("/{project_id}", response_model=List[MemoryItem])
def get_project_memories(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all retained memories from Hindsight for a specific project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    conn = memory_service.check_connection()
    if not conn.get("connected"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Hindsight server is not reachable at {memory_service.base_url}. Please ensure the Hindsight server is running."
        )

    memories = memory_service.list_project_memories(project_id)
    return memories

@router.get("/{project_id}/status", response_model=MemoryBankStatus)
def get_project_bank_status(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check memory bank health, metrics, and categorization for this project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    bank_status = memory_service.get_bank_status(project_id)
    return bank_status

@router.get("/{project_id}/activity", response_model=List[MemoryActivityLog])
def get_memory_activity(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activity log of retained learnings and developer feedback for this project."""
    feedback_records = (
        db.query(ReviewFeedback)
        .join(ReviewFeedback.review)
        .filter(ReviewFeedback.review.has(project_id=project_id))
        .order_by(ReviewFeedback.created_at.desc())
        .limit(30)
        .all()
    )

    activity: List[MemoryActivityLog] = []
    for f in feedback_records:
        activity.append(
            MemoryActivityLog(
                id=str(f.id),
                action="retained" if f.is_retained_in_hindsight else "feedback_recorded",
                content=f"Feedback '{f.feedback_type}' on finding {f.finding_id}: {f.comment or 'Confirmed standard'}",
                category=f.feedback_type,
                timestamp=f.created_at,
                project_id=project_id,
                review_id=f.review_id
            )
        )
    return activity

@router.post("/{project_id}/retain", response_model=Dict[str, Any])
def retain_project_memory(
    project_id: int,
    retain_in: MemoryRetainRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Explicitly retain a project standard, rule, or architectural decision into Hindsight."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    conn = memory_service.check_connection()
    if not conn.get("connected"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot retain memory: Hindsight server is not reachable at {memory_service.base_url}."
        )

    try:
        mem_id = memory_service.retain_memory(
            project_id=project_id,
            content=retain_in.content,
            category=retain_in.category,
            context=retain_in.context,
            tags=retain_in.tags
        )
        return {
            "success": True,
            "bank_id": memory_service.get_bank_id_for_project(project_id),
            "memory_id": mem_id,
            "content": retain_in.content,
            "category": retain_in.category
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hindsight retention failed: {str(e)}"
        )

@router.post("/{project_id}/recall", response_model=List[RecalledMemoryItem])
def recall_project_memories(
    project_id: int,
    recall_in: MemoryRecallRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test recall from Hindsight for a specific query."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    conn = memory_service.check_connection()
    if not conn.get("connected"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot recall memories: Hindsight server is not reachable at {memory_service.base_url}."
        )

    results = memory_service.recall_memories(
        project_id=project_id,
        query=recall_in.query,
        tags=recall_in.tags,
        limit=recall_in.limit or 5
    )
    return results
