import datetime
import uuid
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    languages = Column(JSON, default=list)  # e.g. ["python", "javascript"]
    coding_standards = Column(Text, nullable=True)  # project-specific guidelines
    hindsight_bank_id = Column(String(255), unique=True, nullable=False, index=True, default=lambda: f"reviewmind-project-{uuid.uuid4().hex[:8]}")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="projects")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    settings = relationship("ProjectSettings", back_populates="project", uselist=False, cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="project", cascade="all, delete-orphan")
    github_repositories = relationship("GitHubRepository", back_populates="project")

class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="member")  # owner, admin, member, viewer
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    project = relationship("Project", back_populates="members")

class ProjectSettings(Base):
    __tablename__ = "project_settings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), unique=True, nullable=False)
    auto_review_prs = Column(Boolean, default=False)
    severity_threshold = Column(String(50), default="low")  # critical, high, medium, low, informational
    enabled_categories = Column(JSON, default=lambda: ["security", "bug", "performance", "code_quality", "maintainability"])
    custom_rules = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    project = relationship("Project", back_populates="settings")
