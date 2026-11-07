import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class GitHubTokenInput(BaseModel):
    personal_access_token: str = Field(..., min_length=10, description="GitHub Personal Access Token or OAuth Token")

class GitHubRepoSchema(BaseModel):
    id: str
    name: str
    full_name: str
    default_branch: str
    private: bool
    html_url: str
    description: Optional[str] = None

class GitHubPRSchema(BaseModel):
    id: int
    number: int
    title: str
    state: str
    head_branch: str
    base_branch: str
    author: str
    html_url: str
    diff_url: str
    created_at: str

class GitHubPRFileSchema(BaseModel):
    filename: str
    status: str  # modified, added, removed
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None

class ReviewPRRequest(BaseModel):
    project_id: int
    repo_full_name: str
    pr_number: int

class PublishReviewCommentRequest(BaseModel):
    comment_body: str
    commit_id: Optional[str] = None
    path: Optional[str] = None
    line: Optional[int] = None
