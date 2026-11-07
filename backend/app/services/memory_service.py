import logging
import re
from typing import List, Dict, Any, Optional
import httpx
from hindsight_client import Hindsight
import hindsight_client_api.exceptions as hsk_exceptions
from app.config import settings
from app.schemas.memory import MemoryItem, MemoryBankStatus
from app.schemas.review import RecalledMemoryItem

logger = logging.getLogger(__name__)

# --- Custom Exception Hierarchy for Hindsight ---
class HindsightError(Exception):
    """Base exception for Hindsight agent memory operations."""
    pass

class HindsightAuthenticationError(HindsightError):
    """Raised on HTTP 401: Invalid or missing API key."""
    pass

class HindsightForbiddenError(HindsightError):
    """Raised on HTTP 403: Scope mismatch or permission denied."""
    pass

class HindsightCreditsError(HindsightError):
    """Raised on HTTP 402: Insufficient credits on Vectorize account."""
    pass

class HindsightNotFoundError(HindsightError):
    """Raised on HTTP 404: Bank or memory resource not found."""
    pass

class HindsightTimeoutError(HindsightError):
    """Raised on request timeout."""
    pass

class HindsightConnectionError(HindsightError):
    """Raised when server cannot be reached."""
    pass


class MemoryService:
    """
    Production-grade integration service for Hindsight persistent agent memory.
    Connects to Hindsight Cloud (https://api.hindsight.vectorize.io) or self-hosted instances.
    Provides strict project isolation using dedicated memory banks per project.
    """

    def __init__(self):
        # 1. Normalize Base URL
        raw_url = (settings.HINDSIGHT_BASE_URL or "https://api.hindsight.vectorize.io").strip().rstrip("/")
        # If user configured the inference endpoint URL by mistake, redirect to the official Cloud API endpoint
        if "inference.hindsight.vectorize.io" in raw_url:
            logger.info("Redirecting inference endpoint to official Hindsight Cloud API endpoint (https://api.hindsight.vectorize.io)")
            raw_url = "https://api.hindsight.vectorize.io"
        elif raw_url.endswith("/v1"):
            raw_url = raw_url[:-3]

        self.base_url = raw_url
        self.base_bank_id = (getattr(settings, "HINDSIGHT_BANK_ID", None) or "reviewmind").strip()
        self.api_key = settings.HINDSIGHT_API_KEY
        self.timeout = float(settings.HINDSIGHT_TIMEOUT_SECONDS)

        # Single client instance reused across requests (official SDK best practice)
        self._client: Optional[Hindsight] = None
        self._init_client()

    def _init_client(self):
        """Initialize or re-initialize the singleton Hindsight SDK client."""
        try:
            kwargs = {
                "base_url": self.base_url,
                "timeout": self.timeout,
            }
            if self.api_key:
                kwargs["api_key"] = self.api_key
            self._client = Hindsight(**kwargs)
            logger.info(f"Initialized Hindsight client pointing to {self.base_url}")
        except Exception as e:
            logger.warning(f"Could not initialize Hindsight client: {self._sanitize(str(e))}")
            self._client = None

    def get_client(self) -> Hindsight:
        """Get the active Hindsight client instance or re-initialize if needed."""
        if self._client is None:
            self._init_client()
        if self._client is None:
            raise HindsightConnectionError(
                f"Hindsight client could not be initialized for {self.base_url}."
            )
        return self._client

    def _sanitize(self, message: str) -> str:
        """Ensure API keys and bearer tokens are never printed or leaked in logs or error messages."""
        if not message:
            return ""
        sanitized = message
        if self.api_key:
            sanitized = sanitized.replace(self.api_key, "[REDACTED_API_KEY]")
        # Redact any hsk_... key patterns
        sanitized = re.sub(r"hsk_[a-zA-Z0-9_]{16,64}", "[REDACTED_KEY]", sanitized)
        sanitized = re.sub(r"Bearer\s+[a-zA-Z0-9_\-\.]+", "Bearer [REDACTED]", sanitized)
        return sanitized

    def _classify_exception(self, e: Exception, operation: str, bank_id: str) -> Exception:
        """Classify low-level exceptions into typed, actionable Hindsight exceptions."""
        status = getattr(e, "status", None)
        body = self._sanitize(str(getattr(e, "body", "") or str(e)))

        if isinstance(e, hsk_exceptions.UnauthorizedException) or status == 401:
            return HindsightAuthenticationError(
                f"Hindsight authentication failed (HTTP 401) during {operation} on bank '{bank_id}'. "
                "Check that HINDSIGHT_API_KEY in backend/.env is valid and not expired."
            )

        if isinstance(e, hsk_exceptions.ForbiddenException) or status == 403:
            return HindsightForbiddenError(
                f"Hindsight access forbidden (HTTP 403) during {operation} on bank '{bank_id}'. "
                f"Server message: {body}. "
                "Ensure your API key is created from Hindsight Cloud (ui.hindsight.vectorize.io) with Cloud API scope."
            )

        if status == 402 or "insufficient credits" in body.lower():
            return HindsightCreditsError(
                f"Hindsight Cloud account has insufficient credits (HTTP 402) during {operation}. "
                "Please add credits to your Vectorize / Hindsight Cloud account."
            )

        if isinstance(e, hsk_exceptions.NotFoundException) or status == 404:
            return HindsightNotFoundError(
                f"Hindsight memory bank '{bank_id}' not found (HTTP 404) during {operation}."
            )

        if "timeout" in body.lower() or status in (408, 504):
            return HindsightTimeoutError(
                f"Hindsight request timed out after {self.timeout}s during {operation} on bank '{bank_id}'."
            )

        if "connect" in body.lower() or "connection refused" in body.lower():
            return HindsightConnectionError(
                f"Cannot connect to Hindsight server at {self.base_url} during {operation}."
            )

        return HindsightError(f"Hindsight {operation} error for bank '{bank_id}': {body}")

    def get_bank_id_for_project(self, project_id: int) -> str:
        """
        Derive an isolated memory bank ID for a specific project.
        Enforces project boundary isolation so memories cannot leak across projects.
        """
        return f"{self.base_bank_id}-project-{project_id}"

    def check_connection(self) -> Dict[str, Any]:
        """
        Verify real HTTP connectivity to the Hindsight server and validate API key permissions.
        Never prints or exposes secret credentials.
        """
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            with httpx.Client(timeout=5.0) as http_client:
                # 1. Probe health / ready endpoint
                resp = http_client.get(f"{self.base_url}/health/ready", headers=headers)
                if resp.status_code == 200:
                    return {
                        "connected": True,
                        "base_url": self.base_url,
                        "status_code": 200,
                        "message": "Connected to Hindsight Cloud server"
                    }

                # 2. Probe base / openapi if health/ready returned different status
                resp2 = http_client.get(f"{self.base_url}/openapi.json", headers=headers)
                if resp2.status_code == 200:
                    return {
                        "connected": True,
                        "base_url": self.base_url,
                        "status_code": 200,
                        "message": "Connected to Hindsight API server"
                    }

                # If server responded with an error (e.g. 401 or 403)
                sanitized_body = self._sanitize(resp.text[:200])
                return {
                    "connected": False,
                    "base_url": self.base_url,
                    "status_code": resp.status_code,
                    "error": f"Hindsight server returned HTTP {resp.status_code}: {sanitized_body}"
                }
        except httpx.ConnectError:
            return {
                "connected": False,
                "base_url": self.base_url,
                "error": f"Cannot connect to Hindsight at {self.base_url}. Network unreachable or host down."
            }
        except httpx.TimeoutException:
            return {
                "connected": False,
                "base_url": self.base_url,
                "error": f"Connection to Hindsight at {self.base_url} timed out."
            }
        except Exception as e:
            return {
                "connected": False,
                "base_url": self.base_url,
                "error": self._sanitize(str(e))
            }

    def ensure_bank_exists(self, project_id: int, project_name: str) -> bool:
        """
        Ensure an isolated memory bank exists in Hindsight for the project.
        Uses official SDK `create_bank` method with project metadata.
        Returns True if created or exists, False if service is unreachable or unauthorized.
        """
        bank_id = self.get_bank_id_for_project(project_id)
        try:
            client = self.get_client()
            client.create_bank(
                bank_id=bank_id,
                name=f"ReviewMind: {project_name}",
                mission="Store project coding standards, recurring bugs, resolved vulnerabilities, and developer preferences."
            )
            logger.info(f"Created or updated Hindsight memory bank: {bank_id}")
            return True
        except Exception as e:
            status = getattr(e, "status", None)
            if status in (409, 400):  # Bank already exists or conflict
                logger.info(f"Bank {bank_id} already exists or acknowledged.")
                return True
            classified = self._classify_exception(e, "create_bank", bank_id)
            logger.warning(f"Could not initialize Hindsight bank: {classified}")
            return False

    def recall_memories(
        self,
        project_id: int,
        query: str,
        tags: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[RecalledMemoryItem]:
        """
        Recall relevant project memories from Hindsight using semantic search.
        Strictly isolated to the project's memory bank ID.
        Returns recalled memories or empty list if bank is empty or server unreachable.
        """
        bank_id = self.get_bank_id_for_project(project_id)

        try:
            client = self.get_client()
            recall_resp = client.recall(
                bank_id=bank_id,
                query=query,
                tags=tags if tags else None,
                budget="mid",
                max_tokens=4096
            )

            results: List[RecalledMemoryItem] = []
            if hasattr(recall_resp, "results") and recall_resp.results:
                for r in recall_resp.results[:limit]:
                    score_val = None
                    if hasattr(r, "scores") and r.scores and hasattr(r.scores, "total"):
                        score_val = float(r.scores.total)
                    elif hasattr(r, "score") and r.score:
                        score_val = float(r.score)

                    results.append(
                        RecalledMemoryItem(
                            id=getattr(r, "id", None),
                            text=getattr(r, "text", str(r)),
                            context=getattr(r, "context", None),
                            score=score_val,
                            tags=getattr(r, "tags", None) or []
                        )
                    )
            return results

        except Exception as e:
            status = getattr(e, "status", None)
            # If the bank was never initialized and has 0 memories, 404 is an empty bank
            if isinstance(e, hsk_exceptions.NotFoundException) or status == 404:
                logger.info(f"Hindsight bank {bank_id} has no memories yet.")
                return []
            classified = self._classify_exception(e, "recall", bank_id)
            logger.warning(f"Hindsight recall skipped: {classified}")
            raise classified

    def retain_memory(
        self,
        project_id: int,
        content: str,
        category: str = "coding_standards",
        context: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Retain validated knowledge, project conventions, or bug lessons into Hindsight.
        Associates memory strictly with the project's isolated memory bank.
        """
        client = self.get_client()
        bank_id = self.get_bank_id_for_project(project_id)

        effective_tags = [category]
        for t in (tags or []):
            if t not in effective_tags:
                effective_tags.append(t)
        effective_context = context or f"ReviewMind project {project_id} - {category}"
        metadata = {"project_id": str(project_id), "category": category}

        try:
            retain_resp = client.retain(
                bank_id=bank_id,
                content=content,
                context=effective_context,
                metadata=metadata,
                tags=effective_tags
            )
            memory_id = getattr(retain_resp, "operation_id", None) or getattr(retain_resp, "document_id", None) or "retained"
            logger.info(f"Successfully retained memory in Hindsight bank {bank_id}: {memory_id}")
            return str(memory_id)
        except Exception as e:
            classified = self._classify_exception(e, "retain", bank_id)
            logger.error(f"Hindsight retain error: {classified}")
            raise classified

    def list_project_memories(self, project_id: int) -> List[MemoryItem]:
        """
        List stored memories directly from Hindsight for a specific project.
        """
        client = self.get_client()
        bank_id = self.get_bank_id_for_project(project_id)

        try:
            resp = client.list_memories(bank_id=bank_id, limit=100)
            items: List[MemoryItem] = []
            mem_units = getattr(resp, "items", []) or getattr(resp, "memory_units", []) or []
            for u in mem_units:
                items.append(
                    MemoryItem(
                        id=getattr(u, "id", None),
                        text=getattr(u, "text", "") or getattr(u, "content", ""),
                        category=getattr(u, "context", "general"),
                        tags=getattr(u, "tags", []) or [],
                        created_at=str(getattr(u, "created_at", "")),
                        metadata=getattr(u, "metadata", {}) or {}
                    )
                )
            return items
        except Exception as e:
            status = getattr(e, "status", None)
            if isinstance(e, hsk_exceptions.NotFoundException) or status == 404:
                return []
            classified = self._classify_exception(e, "list_memories", bank_id)
            logger.warning(f"Could not list memories from Hindsight: {classified}")
            raise classified

    def get_bank_status(self, project_id: int) -> MemoryBankStatus:
        """Inspect status and memory categorization of a project's Hindsight memory bank."""
        bank_id = self.get_bank_id_for_project(project_id)
        conn = self.check_connection()
        if not conn.get("connected"):
            return MemoryBankStatus(
                bank_id=bank_id,
                is_connected=False,
                total_memories=0,
                message=conn.get("error", "Hindsight server disconnected")
            )

        try:
            memories = self.list_project_memories(project_id)
            cat_counts: Dict[str, int] = {}
            for m in memories:
                cat = m.category or "general"
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

            return MemoryBankStatus(
                bank_id=bank_id,
                is_connected=True,
                total_memories=len(memories),
                categories=cat_counts,
                message="Connected to Hindsight Cloud server"
            )
        except Exception as e:
            return MemoryBankStatus(
                bank_id=bank_id,
                is_connected=False,
                total_memories=0,
                message=self._sanitize(str(e))
            )

memory_service = MemoryService()
