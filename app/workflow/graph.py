"""
LangGraph Workflow Definition

This file connects all nodes together into a complete workflow.
"""

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from app.workflow.state import GraphState, create_initial_state
from app.workflow.nodes import (
    fetch_linkedin_data,
    analyse_blog_content,
    analyse_company_website,
    analyze_social_media,
    anayse_recent_news,
    generate_digital_presence_report,
    generate_globa_research_report,
    score_lead,
    geenrate_outreach_report,
    generate_interview_script,
    generate_personilized_email,
    save_to_database,
    check_if_qualified,
)


def create_research_workflow() -> StateGraph:
    workflow = StateGraph(GraphState)

    workflow.add_node(
        "fetch_linkedin_data",
        fetch_linkedin_data,
    )
    workflow.add_node(
        "analyse_company_website",
        analyse_company_website,
    )
    workflow.add_node(
        "analyse_blog_content",
        analyse_blog_content,
    )
    workflow.add_node(
        "analyze_social_media",
        analyze_social_media,
    )
    workflow.add_node(
        "analyse_recent_news",
        anayse_recent_news,
    )
    workflow.add_node(
        "generate_digital_presence_report",
        generate_digital_presence_report,
    )
    workflow.add_node(
        "generate_global_research_report",
        generate_globa_research_report,
    )
    workflow.add_node(
        "score_lead",
        score_lead,
    )
    workflow.add_node(
        "generate_outreach_report",
        geenrate_outreach_report,
    )
    workflow.add_node(
        "generate_personalized_email",
        generate_personilized_email,
    )
    workflow.add_node(
        "generate_interview_script",
        generate_interview_script,
    )

    workflow.add_node(
        "save_to_database",
        save_to_database,
    )

    workflow.set_entry_point("fetch_linkedin_data")

    workflow.add_edge("fetch_linkedin_data", "analyse_company_website")
    workflow.add_edge("analyse_company_website", "analyse_blog_content")
    workflow.add_edge("analyse_company_website", "analyze_social_media")
    workflow.add_edge("analyse_company_website", "analyse_recent_news")

    workflow.add_edge("analyse_blog_content", "generate_digital_presence_report")
    workflow.add_edge("analyze_social_media", "generate_digital_presence_report")
    workflow.add_edge("analyse_recent_news", "generate_digital_presence_report")

    workflow.add_edge(
        "generate_digital_presence_report", "generate_global_research_report"
    )
    workflow.add_edge("generate_global_research_report", "score_lead")
    workflow.add_conditional_edges(
        "score_lead",
        check_if_qualified,
        {
            "qualified": "generate_outreach_report",
            "not_qualified": "save_to_database",
        },
    )

    workflow.add_edge("generate_outreach_report", "generate_personalized_email")
    workflow.add_edge("generate_personalized_email", "generate_interview_script")
    workflow.add_edge("generate_interview_script", "save_to_database")
    workflow.add_edge("save_to_database", END)

    return workflow.compile()


research_workflow: CompiledStateGraph = create_research_workflow()


async def run_research_workflow(lead_data: dict, user_id: str) -> GraphState:
    """
    Run the complete research workflow for a lead.

    Args:
        lead_data: Lead information from database
        user_id: The user running the workflow

    Returns:
        Final state after workflow completion
    """

    initial_state = create_initial_state(lead_data, user_id)

    final_state = await research_workflow.ainvoke(initial_state)

    return final_state
