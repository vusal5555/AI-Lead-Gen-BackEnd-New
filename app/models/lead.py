from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class LeadBase(BaseModel):
    """Base lead fields used for creation and updates."""

    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    linkedin_url: Optional[str] = None


class LeadCreate(LeadBase):
    """Schema for creating a new lead."""

    pass


class LeadUpdate(BaseModel):
    """Schema for updating a lead. All fields optional."""

    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    status: Optional[str] = None
    score: Optional[float] = None
    score_details: Optional[Dict[str, Any]] = None


class Lead(LeadBase):
    """Complete lead schema returned from database."""

    id: UUID
    user_id: UUID
    external_id: Optional[str] = None
    status: str = "new"
    score: Optional[float] = None
    score_details: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadWithReports(Lead):
    """Lead with associated reports included."""

    reports: list = []
    company_data: Optional[Dict[str, Any]] = None
