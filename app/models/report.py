from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ReportBase(BaseModel):
    """Base report fields."""

    report_type: str
    title: Optional[str] = None
    content: str
    is_markdown: bool = True
    metadata: Optional[Dict[str, Any]] = None


class ReportCreate(ReportBase):
    """Schema for creating a new report."""

    lead_id: UUID


class Report(ReportBase):
    """Complete report schema returned from database."""

    id: UUID
    lead_id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
