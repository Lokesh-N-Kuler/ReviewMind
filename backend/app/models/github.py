import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class GitHubConnection(Base):
    __tablename__ = "github_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    github_user_id = Column(String(100), nullable=False)
    github_username = Column(String(100), nullable=False)
    encrypted_access_token = Column(Text, nullable=False)  # securely stored token
    token_type = Column(String(50), default="bearer")
    scope = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="github_connection")
    repositories = relationship("GitHubRepository", back_populates="connection", cascade="all, delete-orphan")

class GitHubRepository(Base):
    __tablename__ = "github_repositories"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("github_connections.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    repo_id = Column(String(100), nullable=False)
    repo_name = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    default_branch = Column(String(100), default="main")
    private = Column(Boolean, default=False)
    html_url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    connection = relationship("GitHubConnection", back_populates="repositories")
    project = relationship("Project", back_populates="github_repositories")
    pull_requests = relationship("GitHubPullRequest", back_populates="repository", cascade="all, delete-orphan")

class GitHubPullRequest(Base):
    __tablename__ = "github_pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("github_repositories.id", ondelete="CASCADE"), nullable=False)
    pr_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    state = Column(String(50), default="open")  # open, closed, merged
    head_branch = Column(String(255), nullable=False)
    base_branch = Column(String(255), nullable=False)
    author = Column(String(100), nullable=False)
    html_url = Column(String(500), nullable=False)
    diff_url = Column(String(500), nullable=False)
    last_reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    repository = relationship("GitHubRepository", back_populates="pull_requests")
