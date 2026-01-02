from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class JobBase(BaseModel):
    """Base job fields."""

    job_type: str
    lead_id: Optional[UUID] = None


class JobCreate(JobBase):
    """Schema for creating a new job."""

    pass


class JobUpdate(BaseModel):
    """Schema for updating job status."""

    status: Optional[str] = None
    current_step: Optional[str] = None
    progress: Optional[int] = None
    total_steps: Optional[int] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class Job(JobBase):
    """Complete job schema returned from database."""

    id: UUID
    user_id: UUID
    status: str = "pending"
    current_step: Optional[str] = None
    progress: int = 0
    total_steps: int = 0
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
