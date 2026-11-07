import logging
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings
from app.utils.security import decrypt_token

logger = logging.getLogger(__name__)

class GitHubService:
    GITHUB_API_BASE = "https://api.github.com"

    def get_headers(self, encrypted_token: str) -> Dict[str, str]:
        token = decrypt_token(encrypted_token)
        return {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ReviewMind-AI-Agent",
        }

    async def verify_token_and_get_user(self, token: str) -> Dict[str, Any]:
        """Validate token by calling /user."""
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ReviewMind-AI-Agent",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.GITHUB_API_BASE}/user", headers=headers)
            if resp.status_code != 200:
                raise ValueError(f"GitHub token verification failed: HTTP {resp.status_code} - {resp.text}")
            return resp.json()

    async def list_repositories(self, encrypted_token: str) -> List[Dict[str, Any]]:
        """List repositories accessible to the user."""
        headers = self.get_headers(encrypted_token)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.GITHUB_API_BASE}/user/repos?sort=updated&per_page=50",
                headers=headers
            )
            if resp.status_code != 200:
                logger.error(f"Failed to list GitHub repos: {resp.status_code} {resp.text}")
                return []
            repos = resp.json()
            return [
                {
                    "id": str(r["id"]),
                    "name": r["name"],
                    "full_name": r["full_name"],
                    "default_branch": r.get("default_branch", "main"),
                    "private": r.get("private", False),
                    "html_url": r.get("html_url", ""),
                    "description": r.get("description", "")
                }
                for r in repos
            ]

    async def list_pull_requests(self, encrypted_token: str, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Fetch open pull requests for a repository."""
        headers = self.get_headers(encrypted_token)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/pulls?state=open",
                headers=headers
            )
            if resp.status_code != 200:
                logger.error(f"Failed to fetch PRs: {resp.status_code} {resp.text}")
                return []
            prs = resp.json()
            return [
                {
                    "id": pr["id"],
                    "number": pr["number"],
                    "title": pr["title"],
                    "state": pr["state"],
                    "head_branch": pr["head"]["ref"],
                    "base_branch": pr["base"]["ref"],
                    "author": pr["user"]["login"],
                    "html_url": pr["html_url"],
                    "diff_url": pr["diff_url"],
                    "created_at": pr["created_at"],
                }
                for pr in prs
            ]

    async def get_pull_request_files(self, encrypted_token: str, owner: str, repo: str, pull_number: int) -> List[Dict[str, Any]]:
        """Fetch changed files and patches for a PR."""
        headers = self.get_headers(encrypted_token)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pull_number}/files",
                headers=headers
            )
            if resp.status_code != 200:
                raise ValueError(f"Failed to fetch PR files: {resp.status_code} {resp.text}")
            files = resp.json()
            return [
                {
                    "filename": f["filename"],
                    "status": f.get("status", "modified"),
                    "additions": f.get("additions", 0),
                    "deletions": f.get("deletions", 0),
                    "changes": f.get("changes", 0),
                    "patch": f.get("patch", ""),
                }
                for f in files
            ]

    async def publish_comment(
        self,
        encrypted_token: str,
        owner: str,
        repo: str,
        pull_number: int,
        body: str,
        commit_id: Optional[str] = None,
        path: Optional[str] = None,
        line: Optional[int] = None
    ) -> Dict[str, Any]:
        """Publish an explicitly approved comment to a GitHub PR."""
        headers = self.get_headers(encrypted_token)
        async with httpx.AsyncClient(timeout=15.0) as client:
            # If path and line are specified, post as an inline review comment
            if path and line and commit_id:
                url = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pull_number}/comments"
                payload = {
                    "body": body,
                    "commit_id": commit_id,
                    "path": path,
                    "line": line,
                    "side": "RIGHT"
                }
            else:
                # Post as issue/PR discussion comment
                url = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{pull_number}/comments"
                payload = {"body": body}

            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code not in (200, 201):
                raise ValueError(f"Failed to publish GitHub comment: {resp.status_code} {resp.text}")
            return resp.json()

github_service = GitHubService()
