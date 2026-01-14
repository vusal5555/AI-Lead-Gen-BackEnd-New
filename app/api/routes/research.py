from fastapi import APIRouter, HTTPException
from app.database import get_supabase_client
from pydantic import BaseModel
from app.workflow.graph import run_research_workflow


router = APIRouter()


class ResearchRequest(BaseModel):
    lead_id: str


@router.post("/start")
async def start_research(request: ResearchRequest):
    """
    Start research workflow for a lead.
    """

    try:

        supabase = get_supabase_client()

        result = supabase.table("leads").select("*").eq("id", request.lead_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        lead = result.data[0]

        print(f"Starting research for lead ID: {request.lead_id}")

        supabase.table("leads").update({"status": "researching"}).eq(
            "id", request.lead_id
        ).execute()

        final_state = await run_research_workflow(lead, lead.get("user_id", ""))

        leads_update = {
            "status": (
                "qualified"
                if final_state.get("is_qualified", False)
                else "not_qualified"
            ),
            "score": final_state.get("lead_score", 0.0),
            "score_details": final_state.get("score_details"),
        }

        supabase.table("leads").update(leads_update).eq("id", request.lead_id).execute()

        return {
            "message": "Research completed",
            "lead_id": request.lead_id,
            "is_qualified": final_state.get("is_qualified", False),
            "score": final_state.get("lead_score"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{lead_id}")
async def get_research_status(lead_id: str):
    """
    Get the research status of a lead.
    """

    try:
        supabase = get_supabase_client()

        result = supabase.table("leads").select("*").eq("id", lead_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        lead = result.data[0]

        return {
            "lead": lead,
            "status": lead.get("status", "unknown"),
            "score": lead.get("score"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{lead_id}")
async def get_research_reports(lead_id: str):
    """Get all reports for a lead."""

    try:
        supabase = get_supabase_client()

        result = supabase.table("reports").select("*").eq("lead_id", lead_id).execute()

        return {"reports": result.data or []}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
