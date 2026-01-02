"""
LangGraph State Definition

This file defines the data structure that flows through the workflow.
Each node receives this state and can update parts of it.
"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from operator import add


class SocialMediaLinks(TypedDict, total=False):
    """Social media URLs for a company."""

    blog: str
    facebook: str
    twitter: str
    youtube: str


class LeadInfo(TypedDict, total=False):
    """Information about the lead being processed."""

    id: str
    name: str
    email: str
    phone: str
    address: str
    company_name: str
    company_website: str
    linkedin_url: str


class CompanyInfo(TypedDict, total=False):
    """Information about the lead's company."""

    name: str
    profile: str
    website: str
    linkedin_url: str
    social_media_links: SocialMediaLinks
    raw_data: Dict[str, Any]


class Report(TypedDict):
    """A generated report."""

    report_type: str
    title: str
    content: str
    is_markdown: bool
    metadata: Dict[str, Any]


class OutreachMaterials(TypedDict, total=False):
    """Generated outreach materials."""

    outreach_report: str
    email_subject: str
    email_body: str
    interview_script: str


class GraphState(TypedDict, total=False):
    """
    Complete state that flows through the LangGraph workflow.

    Annotated[List, add] means nodes can append to lists
    instead of replacing them.
    """

    # Context
    user_id: str
    current_lead: LeadInfo
    company_data: CompanyInfo

    # Research results
    linkedin_profile: str
    website_analysis: str
    blog_analysis: str
    social_media_analysis: str
    news_analysis: str
    digital_presence_report: str
    global_research_report: str

    # Reports - using add operator for appending
    reports: Annotated[List[Report], add]

    # Scoring
    lead_score: float
    score_details: Dict[str, Any]
    is_qualified: bool

    # Outreach
    outreach_materials: OutreachMaterials

    # Tracking
    current_step: str
    errors: Annotated[List[str], add]
    completed_steps: Annotated[List[str], add]


def create_initial_state(lead_data: Dict[str, Any], user_id: str) -> GraphState:
    """Create initial state for a new workflow run."""
    return GraphState(
        user_id=user_id,
        current_lead=LeadInfo(
            id=lead_data.get("id", ""),
            name=lead_data.get("name", ""),
            email=lead_data.get("email", ""),
            phone=lead_data.get("phone", ""),
            address=lead_data.get("address", ""),
            company_name=lead_data.get("company_name", ""),
            company_website=lead_data.get("company_website", ""),
            linkedin_url=lead_data.get("linkedin_url", ""),
        ),
        company_data=CompanyInfo(
            name=lead_data.get("company_name", ""),
            website=lead_data.get("company_website", ""),
            social_media_links=SocialMediaLinks(),
        ),
        linkedin_profile="",
        website_analysis="",
        blog_analysis="",
        social_media_analysis="",
        news_analysis="",
        digital_presence_report="",
        global_research_report="",
        reports=[],
        lead_score=0.0,
        score_details={},
        is_qualified=False,
        outreach_materials=OutreachMaterials(),
        current_step="initialized",
        errors=[],
        completed_steps=[],
    )
