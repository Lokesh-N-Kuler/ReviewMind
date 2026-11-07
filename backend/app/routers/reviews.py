from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.review import Review, ReviewFinding
from app.models.feedback import ReviewFeedback
from app.schemas.review import (
    ReviewCreateRequest,
    QuickReviewRequest,
    ReviewResponse,
    FindingSchema,
    FeedbackCreateRequest,
    FeedbackResponse,
)
from app.routers.auth import get_current_user, get_optional_user
from app.services.review_service import review_service
from app.services.memory_service import memory_service

router = APIRouter(prefix="/api/reviews", tags=["Code Reviews"])

@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    review_in: ReviewCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify project exists and user has access
    project = db.query(Project).filter(Project.id == review_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    is_member = (
        project.owner_id == current_user.id or
        any(m.user_id == current_user.id for m in project.members)
    )
    if not is_member:
        raise HTTPException(status_code=403, detail="Not authorized to submit reviews for this project.")

    # Execute review orchestrator
    review_record = review_service.perform_review(
        db=db,
        project_id=review_in.project_id,
        user_id=current_user.id,
        source_code=review_in.source_code,
        language=review_in.language,
        title=review_in.title or f"{review_in.language.capitalize()} Review",
        file_path=review_in.file_path or "main"
    )

    return review_service.format_review_response(review_record)

@router.post("/quick", response_model=ReviewResponse)
def quick_review(
    review_in: QuickReviewRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Perform a review without creating a project first (using default demo project or temporary context)."""
    user_id = current_user.id if current_user else 1

    # Find or create a default sandbox project for quick testing
    project_id = review_in.project_id
    if not project_id:
        sandbox_project = db.query(Project).filter(Project.name == "Playground Project").first()
        if not sandbox_project:
            # Create a system demo user if needed
            demo_user = db.query(User).first()
            if not demo_user:
                from app.utils.security import get_password_hash
                demo_user = User(
                    email="developer@reviewmind.ai",
                    hashed_password=get_password_hash("password123"),
                    full_name="Lead Developer"
                )
                db.add(demo_user)
                db.flush()

            sandbox_project = Project(
                name="Playground Project",
                description="Default sandbox project for instant interactive code reviews.",
                owner_id=demo_user.id,
                languages=["python", "javascript", "typescript", "sql", "java", "cpp"],
                coding_standards="Enforce parameterized queries for database operations. Avoid eval and insecure deserialization.",
                hindsight_bank_id="reviewmind-playground-bank"
            )
            db.add(sandbox_project)
            db.commit()
            db.refresh(sandbox_project)

        project_id = sandbox_project.id
        user_id = demo_user.id if not current_user else current_user.id

    review_record = review_service.perform_review(
        db=db,
        project_id=project_id,
        user_id=user_id,
        source_code=review_in.source_code,
        language=review_in.language,
        title=f"Instant {review_in.language.capitalize()} Review",
        file_path=review_in.file_path or "main"
    )

    return review_service.format_review_response(review_record)

@router.get("", response_model=List[ReviewResponse])
def list_reviews(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Review).order_by(Review.created_at.desc())

    if project_id:
        query = query.filter(Review.project_id == project_id)
    else:
        # Filter to projects accessible to current user
        user_project_ids = [
            p.id for p in db.query(Project).filter(
                (Project.owner_id == current_user.id) |
                (Project.members.any(ProjectMember.user_id == current_user.id))
            ).all()
        ]
        query = query.filter(Review.project_id.in_(user_project_ids))

    reviews = query.limit(limit).all()

    # In-memory filter for severity if requested
    results = []
    for r in reviews:
        resp = review_service.format_review_response(r)
        if severity:
            sev_lower = severity.lower()
            if not any(f.severity == sev_lower for f in resp.findings):
                continue
        results.append(resp)

    return results

@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found.")

    return review_service.format_review_response(review)

@router.get("/{review_id}/findings", response_model=List[FindingSchema])
def get_review_findings(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found.")

    findings_schemas = []
    for f in review.findings:
        findings_schemas.append(
            FindingSchema(
                finding_id=f.finding_id,
                title=f.title,
                category=f.category,
                severity=f.severity,
                file_path=f.file_path,
                line_start=f.line_start,
                line_end=f.line_end,
                explanation=f.explanation,
                why_it_matters=f.why_it_matters,
                suggested_fix=f.suggested_fix,
                corrected_code=f.corrected_code,
                confidence=f.confidence,
                memory_references=f.memory_references or []
            )
        )
    return findings_schemas

@router.post("/{review_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(
    review_id: int,
    feedback_in: FeedbackCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record developer feedback on a finding and retain confirmed knowledge in Hindsight."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found.")

    finding = db.query(ReviewFinding).filter(
        ReviewFinding.review_id == review_id,
        ReviewFinding.finding_id == feedback_in.finding_id
    ).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found in this review.")

    # Retain useful lessons in Hindsight
    retained_in_hindsight = False
    hindsight_mem_id = None

    if feedback_in.retain_in_hindsight:
        try:
            if feedback_in.feedback_type in ("accepted", "helpful"):
                lesson = (
                    f"Team Rule / Confirmed Fix ({finding.category.upper()}): {finding.title}. "
                    f"Issue: {finding.explanation} "
                    f"Approved Fix: {finding.suggested_fix}"
                )
                category = "coding_standards" if finding.category == "project_standards" else "recurring_bugs"
                hindsight_mem_id = memory_service.retain_memory(
                    project_id=review.project_id,
                    content=lesson,
                    category=category,
                    context=f"Approved in review #{review.id} for finding {finding.finding_id}",
                    tags=[finding.category, finding.severity, "developer_accepted", f"project_{review.project_id}"]
                )
                retained_in_hindsight = True

            elif feedback_in.feedback_type in ("rejected", "false_positive"):
                note = (
                    f"Developer Exception / Rule Override: Finding '{finding.title}' was marked as {feedback_in.feedback_type}. "
                    f"Developer note: {feedback_in.comment or 'False positive in this architecture.'} "
                    f"Do not flag this pattern as a critical violation in this context."
                )
                hindsight_mem_id = memory_service.retain_memory(
                    project_id=review.project_id,
                    content=note,
                    category="developer_preferences",
                    context=f"Developer rejected finding {finding.finding_id}",
                    tags=["preference", "exception", finding.category, f"project_{review.project_id}"]
                )
                retained_in_hindsight = True
        except Exception as e:
            # If Hindsight is disconnected, log error - do not fake retention
            retained_in_hindsight = False
            hindsight_mem_id = None

    # Store feedback record in database
    feedback_record = ReviewFeedback(
        review_id=review_id,
        finding_id=feedback_in.finding_id,
        user_id=current_user.id,
        feedback_type=feedback_in.feedback_type,
        comment=feedback_in.comment,
        is_retained_in_hindsight=retained_in_hindsight,
        hindsight_memory_id=hindsight_mem_id
    )
    db.add(feedback_record)
    db.commit()
    db.refresh(feedback_record)

    return FeedbackResponse(
        id=feedback_record.id,
        review_id=feedback_record.review_id,
        finding_id=feedback_record.finding_id,
        user_id=feedback_record.user_id,
        feedback_type=feedback_record.feedback_type,
        comment=feedback_record.comment,
        is_retained_in_hindsight=feedback_record.is_retained_in_hindsight,
        hindsight_memory_id=feedback_record.hindsight_memory_id,
        created_at=feedback_record.created_at
    )
