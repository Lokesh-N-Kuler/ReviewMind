import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MemoryItem(BaseModel):
    id: Optional[str] = None
    text: str
    category: Optional[str] = "general"
    tags: List[str] = Field(default_factory=list)
    context: Optional[str] = None
    created_at: Optional[str] = None
    score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MemoryRetainRequest(BaseModel):
    content: str = Field(..., min_length=3, description="Knowledge, coding standard, or bug lesson to retain")
    category: str = Field(default="coding_standards", description="coding_standards, recurring_bugs, vulnerabilities, preferences, architecture")
    context: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class MemoryRecallRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Query to recall relevant memories")
    tags: Optional[List[str]] = None
    limit: Optional[int] = 5

class MemoryBankStatus(BaseModel):
    bank_id: str
    is_connected: bool
    total_memories: int
    categories: Dict[str, int] = Field(default_factory=dict)
    message: Optional[str] = None

class MemoryActivityLog(BaseModel):
    id: str
    action: str  # "retained", "recalled"
    content: str
    category: Optional[str] = None
    timestamp: datetime.datetime
    project_id: int
    review_id: Optional[int] = None
