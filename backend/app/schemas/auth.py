import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password at least 6 characters")
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

TokenResponse.model_rebuild()
