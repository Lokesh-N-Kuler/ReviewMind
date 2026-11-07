import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    languages: List[str] = Field(default_factory=lambda: ["python"])
    coding_standards: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    languages: Optional[List[str]] = None
    coding_standards: Optional[str] = None

class ProjectSettingsSchema(BaseModel):
    auto_review_prs: bool = False
    severity_threshold: str = "low"
    enabled_categories: List[str] = Field(default_factory=lambda: ["security", "bug", "performance", "code_quality", "maintainability"])
    custom_rules: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    hindsight_bank_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    settings: Optional[ProjectSettingsSchema] = None
    reviews_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
