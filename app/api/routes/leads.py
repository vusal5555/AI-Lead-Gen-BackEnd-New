from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from uuid import UUID
from app.models.lead import Lead, LeadCreate, LeadUpdate
from app.database import get_supabase_admin_client, get_supabase_client


router = APIRouter()


@router.get("/", response_model=List[Lead])
async def get_leads(limit: int = 5):
    """
    Retrieve all leads from the database.

    Returns:
        List[Lead]: A list of lead objects.
    """
    try:
        supabase = get_supabase_admin_client()
        query = supabase.table("leads").select("*").order("created_at", desc=True)

        if limit:
            query = query.limit(limit)

        response = query.execute()

        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_lead_stats():
    """Get lead statistics."""

    try:
        supabase = get_supabase_admin_client()

        result = supabase.table("leads").select("status, score").execute()

        leads = result.data or []

        scores = []

        stats = {
            "total": len(leads),
            "new": 0,
            "researching": 0,
            "qualified": 0,
            "not_qualified": 0,
            "average_score": 0,
            "conversion_rate": 0,
        }

        for lead in leads:
            status = lead.get("status", "new")

            if status in stats:
                stats[status] += 1

            score = lead.get("score")
            if score is not None and score > 0:
                scores.append(score)

        if scores:
            stats["average_score"] = round(sum(scores) / len(scores), 1)

        completed = stats["qualified"] + stats["not_qualified"]
        if completed > 0:
            stats["conversion_rate"] = round((stats["qualified"] / completed) * 100, 1)

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}", response_model=Lead)
async def get_lead(lead_id: UUID):
    """
    Retrieve a single lead by its ID.

    Args:
        lead_id (UUID): The ID of the lead to retrieve.

    Returns:
        Lead: The lead object.

    Raises:
        HTTPException: If the lead is not found.
    """
    supabase = get_supabase_admin_client()
    response = (
        supabase.table("leads").select("*").eq("id", str(lead_id)).single().execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Lead not found")

    return response.data


@router.post("/", response_model=Lead)
async def create_lead(lead: LeadCreate):

    user_id = str(uuid.uuid4())  # Placeholder for user ID
    """
    Create a new lead.

    Later we'll add:
    - User authentication (associate with user)
    - Validation
    """
    supabase = get_supabase_admin_client()

    # For now, we'll use a placeholder user_id
    # This will be replaced with actual auth later
    lead_data = lead.model_dump()
    lead_data["user_id"] = user_id  # Placeholder

    response = supabase.table("leads").insert(lead_data).execute()

    return response.data[0]


@router.put("/{lead_id}", response_model=Lead)
async def update_lead(lead_id: UUID, lead_update: LeadUpdate):
    """Update an existing lead."""
    supabase = get_supabase_admin_client()

    update_data = lead_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update provided")

    response = (
        supabase.table("leads").update(update_data).eq("id", str(lead_id)).execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Lead not found")

    return response.data[0]


@router.delete("/{lead_id}")
async def delete_lead(lead_id: UUID):
    """Delete a lead."""
    supabase = get_supabase_admin_client()

    response = supabase.table("leads").delete().eq("id", str(lead_id)).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {"message": "Lead deleted successfully"}
