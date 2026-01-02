from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class CompanyDataBase(BaseModel):
    """Base company data fields."""

    name: Optional[str] = None
    profile: Optional[str] = None
    website: Optional[str] = None
    blog_url: Optional[str] = None
    facebook_url: Optional[str] = None
    twitter_url: Optional[str] = None
    youtube_url: Optional[str] = None


class CompanyDataCreate(CompanyDataBase):
    """Schema for creating company data."""

    lead_id: UUID


class CompanyDataUpdate(CompanyDataBase):
    """Schema for updating company data."""

    raw_linkedin_data: Optional[Dict[str, Any]] = None
    raw_website_data: Optional[Dict[str, Any]] = None


class CompanyData(CompanyDataBase):
    """Complete company data schema."""

    id: UUID
    lead_id: UUID
    raw_linkedin_data: Optional[Dict[str, Any]] = None
    raw_website_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
