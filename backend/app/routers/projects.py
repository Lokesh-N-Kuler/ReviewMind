from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember, ProjectSettings
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectSettingsSchema
from app.routers.auth import get_current_user
from app.services.memory_service import memory_service

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Create project record
    bank_id = f"reviewmind-project-user{current_user.id}-{project_in.name.lower().replace(' ', '-')}"
    
    project = Project(
        name=project_in.name,
        description=project_in.description,
        owner_id=current_user.id,
        languages=project_in.languages,
        coding_standards=project_in.coding_standards,
        hindsight_bank_id=bank_id
    )
    db.add(project)
    db.flush()

    # Assign correct ID-based bank ID
    actual_bank_id = memory_service.get_bank_id_for_project(project.id)
    project.hindsight_bank_id = actual_bank_id

    # Create owner membership
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="owner"
    )
    db.add(member)

    # Create default project settings
    project_settings = ProjectSettings(
        project_id=project.id,
        auto_review_prs=False,
        severity_threshold="low",
        enabled_categories=["security", "bug", "performance", "code_quality", "maintainability"],
        custom_rules=project_in.coding_standards
    )
    db.add(project_settings)

    db.commit()
    db.refresh(project)

    # Initialize dedicated Hindsight memory bank for this project
    memory_service.ensure_bank_exists(project.id, project.name)

    # If coding standards provided, retain initial standard in Hindsight
    if project.coding_standards:
        try:
            memory_service.retain_memory(
                project_id=project.id,
                content=f"Initial project coding standards: {project.coding_standards}",
                category="coding_standards",
                tags=["standards", "setup"]
            )
        except Exception:
            pass  # Do not block project creation if Hindsight is unreachable

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        languages=project.languages or ["python"],
        coding_standards=project.coding_standards,
        owner_id=project.owner_id,
        hindsight_bank_id=project.hindsight_bank_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        settings=ProjectSettingsSchema.model_validate(project.settings) if project.settings else None,
        reviews_count=0
    )

@router.get("", response_model=List[ProjectResponse])
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch projects where user is owner or member
    projects = (
        db.query(Project)
        .outerjoin(ProjectMember, Project.id == ProjectMember.project_id)
        .filter((Project.owner_id == current_user.id) | (ProjectMember.user_id == current_user.id))
        .distinct()
        .all()
    )

    results = []
    for p in projects:
        results.append(
            ProjectResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                languages=p.languages or ["python"],
                coding_standards=p.coding_standards,
                owner_id=p.owner_id,
                hindsight_bank_id=p.hindsight_bank_id,
                created_at=p.created_at,
                updated_at=p.updated_at,
                settings=ProjectSettingsSchema.model_validate(p.settings) if p.settings else None,
                reviews_count=len(p.reviews) if p.reviews else 0
            )
        )
    return results

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Authorization check
    is_member = (
        project.owner_id == current_user.id or
        any(m.user_id == current_user.id for m in project.members)
    )
    if not is_member:
        raise HTTPException(status_code=403, detail="Not authorized to access this project.")

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        languages=project.languages or ["python"],
        coding_standards=project.coding_standards,
        owner_id=project.owner_id,
        hindsight_bank_id=project.hindsight_bank_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        settings=ProjectSettingsSchema.model_validate(project.settings) if project.settings else None,
        reviews_count=len(project.reviews) if project.reviews else 0
    )

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only project owners can modify project details.")

    if project_in.name is not None:
        project.name = project_in.name
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.languages is not None:
        project.languages = project_in.languages
    if project_in.coding_standards is not None:
        project.coding_standards = project_in.coding_standards
        # If updated coding standards, retain in Hindsight
        try:
            memory_service.retain_memory(
                project_id=project.id,
                content=f"Updated project coding standards: {project.coding_standards}",
                category="coding_standards",
                tags=["standards", "update"]
            )
        except Exception:
            pass

    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        languages=project.languages or ["python"],
        coding_standards=project.coding_standards,
        owner_id=project.owner_id,
        hindsight_bank_id=project.hindsight_bank_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        settings=ProjectSettingsSchema.model_validate(project.settings) if project.settings else None,
        reviews_count=len(project.reviews) if project.reviews else 0
    )

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only project owners can delete projects.")

    db.delete(project)
    db.commit()
    return None
