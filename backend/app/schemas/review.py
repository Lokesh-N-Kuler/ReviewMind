import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

SeverityLevel = Literal["critical", "high", "medium", "low", "informational"]
CategoryType = Literal[
    "bug",
    "security",
    "performance",
    "code_quality",
    "maintainability",
    "error_handling",
    "input_validation",
    "duplicated_code",
    "edge_cases",
    "project_standards",
]

class FindingSchema(BaseModel):
    finding_id: str = Field(..., description="Unique finding ID like FIND-001")
    title: str = Field(..., description="Short descriptive title of the issue")
    category: CategoryType = Field(..., description="Issue category")
    severity: SeverityLevel = Field(..., description="Severity level")
    file_path: Optional[str] = Field(default="main", description="Target file path")
    line_start: Optional[int] = Field(None, description="Starting line number (1-indexed)")
    line_end: Optional[int] = Field(None, description="Ending line number (1-indexed)")
    explanation: str = Field(..., description="Clear explanation of the problem")
    why_it_matters: str = Field(..., description="Why this issue matters and impact")
    suggested_fix: str = Field(..., description="Step-by-step guidance on how to fix")
    corrected_code: Optional[str] = Field(None, description="Drop-in corrected replacement code snippet")
    confidence: float = Field(0.9, ge=0.0, le=1.0, description="Confidence level between 0 and 1")
    memory_references: List[str] = Field(default_factory=list, description="IDs or quotes of recalled memories applied to this finding")

class AIReviewOutput(BaseModel):
    summary: str = Field(..., description="High-level evaluation summary of the submitted code")
    score: float = Field(100.0, ge=0.0, le=100.0, description="Overall code quality score 0-100")
    findings: List[FindingSchema] = Field(default_factory=list, description="List of detected findings")

class ReviewCreateRequest(BaseModel):
    project_id: int
    title: Optional[str] = "Code Review"
    language: str = Field(..., description="Programming language: python, javascript, typescript, java, cpp, sql")
    source_code: str = Field(..., min_length=1, description="Raw source code to review")
    file_path: Optional[str] = "main"

class QuickReviewRequest(BaseModel):
    language: str
    source_code: str
    file_path: Optional[str] = "main"
    project_id: Optional[int] = None

class ReviewMetrics(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    informational: int = 0
    total: int = 0

class RecalledMemoryItem(BaseModel):
    id: Optional[str] = None
    text: str
    context: Optional[str] = None
    score: Optional[float] = None
    tags: Optional[List[str]] = None

class ReviewResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    title: str
    language: str
    source_code: str
    file_path: Optional[str] = "main"
    status: str
    score: float
    summary: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    recalled_memories: List[RecalledMemoryItem] = Field(default_factory=list)
    retained_memories: List[str] = Field(default_factory=list)
    memory_status: str = Field(default="active")
    findings: List[FindingSchema] = Field(default_factory=list)
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

class FeedbackCreateRequest(BaseModel):
    finding_id: str
    feedback_type: Literal["accepted", "rejected", "false_positive", "helpful"]
    comment: Optional[str] = None
    retain_in_hindsight: bool = True

class FeedbackResponse(BaseModel):
    id: int
    review_id: int
    finding_id: str
    user_id: int
    feedback_type: str
    comment: Optional[str] = None
    is_retained_in_hindsight: bool
    hindsight_memory_id: Optional[str] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
