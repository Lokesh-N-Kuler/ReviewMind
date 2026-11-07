from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.github import GitHubConnection
from app.models.review import Review
from app.schemas.github import (
    GitHubTokenInput,
    GitHubRepoSchema,
    GitHubPRSchema,
    GitHubPRFileSchema,
    ReviewPRRequest,
    PublishReviewCommentRequest,
)
from app.schemas.review import ReviewResponse
from app.routers.auth import get_current_user
from app.services.github_service import github_service
from app.services.review_service import review_service
from app.utils.security import encrypt_token
from app.config import settings

router = APIRouter(prefix="/api/github", tags=["GitHub Integration"])

@router.get("/status", response_model=Dict[str, Any])
def get_github_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if the current user has connected their GitHub account."""
    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == current_user.id).first()
    if not conn:
        return {
            "connected": False,
            "oauth_configured": bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET)
        }
    return {
        "connected": True,
        "github_username": conn.github_username,
        "github_user_id": conn.github_user_id,
        "scope": conn.scope,
        "connected_at": conn.created_at
    }

@router.post("/connect-token", response_model=Dict[str, Any])
async def connect_with_token(
    token_in: GitHubTokenInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Securely connect GitHub using a Personal Access Token."""
    try:
        gh_user = await github_service.verify_token_and_get_user(token_in.personal_access_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid GitHub Token: {str(e)}"
        )

    encrypted_token = encrypt_token(token_in.personal_access_token)
    
    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == current_user.id).first()
    if conn:
        conn.github_user_id = str(gh_user["id"])
        conn.github_username = gh_user["login"]
        conn.encrypted_access_token = encrypted_token
    else:
        conn = GitHubConnection(
            user_id=current_user.id,
            github_user_id=str(gh_user["id"]),
            github_username=gh_user["login"],
            encrypted_access_token=encrypted_token,
            scope="repo"
        )
        db.add(conn)

    db.commit()
    return {
        "connected": True,
        "username": gh_user["login"],
        "message": "GitHub account successfully connected."
    }

@router.delete("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_github(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == current_user.id).first()
    if conn:
        db.delete(conn)
        db.commit()
    return None

@router.get("/repositories", response_model=List[GitHubRepoSchema])
async def list_repositories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == current_user.id).first()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub is not connected. Please connect your GitHub account in Settings."
        )

    repos = await github_service.list_repositories(conn.encrypted_access_token)
    return [GitHubRepoSchema(**r) for r in repos]

@router.get("/repositories/{owner}/{repo}/pull-requests", response_model=List[GitHubPRSchema])
async def list_pull_requests(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == current_user.id).first()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub is not connected."
        )

    prs = await github_service.list_pull_requests(conn.encrypted_access_token, owner, repo)
    return [GitHubPRSchema(**p) for p in prs]

@router.get("/repositories/{owner}/{repo}/pull-requests/{pr_number}/files", response_model=List[GitHubPRFileSchema])
async def get_pr_files(
    owner: str,
    repo: str,
    pr_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == current_user.id).first()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub is not connected."
        )

    files = await github_service.get_pull_request_files(conn.encrypted_access_token, owner, repo, pr_number)
    return [GitHubPRFileSchema(**f) for f in files]

@router.post("/pull-requests/review", response_model=ReviewResponse)
async def review_pull_request(
    review_req: ReviewPRRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == current_user.id).first()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub is not connected."
        )

    parts = review_req.repo_full_name.split("/")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid repo_full_name. Must be 'owner/repo'.")
    owner, repo = parts

    files = await github_service.get_pull_request_files(
        conn.encrypted_access_token, owner, repo, review_req.pr_number
    )
    if not files:
        raise HTTPException(status_code=404, detail="No changed files found in this Pull Request.")

    # Combine patches/code from modified files
    combined_code = []
    primary_lang = "python"
    for f in files:
        patch = f.get("patch") or ""
        fname = f.get("filename", "")
        if fname.endswith((".js", ".jsx")):
            primary_lang = "javascript"
        elif fname.endswith((".ts", ".tsx")):
            primary_lang = "typescript"
        elif fname.endswith(".sql"):
            primary_lang = "sql"
        elif fname.endswith(".java"):
            primary_lang = "java"
        elif fname.endswith((".cpp", ".c", ".h")):
            primary_lang = "cpp"
        
        combined_code.append(f"# File: {fname}\n{patch}")

    source_code = "\n\n".join(combined_code)

    review_record = review_service.perform_review(
        db=db,
        project_id=review_req.project_id,
        user_id=current_user.id,
        source_code=source_code,
        language=primary_lang,
        title=f"PR #{review_req.pr_number} Review ({review_req.repo_full_name})",
        file_path=files[0]["filename"] if files else "pr_diff"
    )

    return review_service.format_review_response(review_record)

@router.post("/reviews/{review_id}/publish", response_model=Dict[str, Any])
async def publish_comment_to_github(
    review_id: int,
    pub_req: PublishReviewCommentRequest,
    repo_full_name: str,
    pr_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Publish an explicitly developer-approved comment to GitHub."""
    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == current_user.id).first()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub is not connected."
        )

    parts = repo_full_name.split("/")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid repo_full_name.")
    owner, repo = parts

    result = await github_service.publish_comment(
        encrypted_token=conn.encrypted_access_token,
        owner=owner,
        repo=repo,
        pull_number=pr_number,
        body=pub_req.comment_body,
        commit_id=pub_req.commit_id,
        path=pub_req.path,
        line=pub_req.line
    )

    return {
        "success": True,
        "comment_id": result.get("id"),
        "html_url": result.get("html_url"),
        "message": "Review comment successfully published to GitHub."
    }
