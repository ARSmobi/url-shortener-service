from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LinkBase(BaseModel):
    original_url: str

class LinkCreate(LinkBase):
    pass

class LinkOut(LinkBase):
    id: int
    short_url: str
    clicks: int
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True
