from app.workflow.state import (
    GraphState,
    OutreachMaterials,
    Report,
    CompanyInfo,
    SocialMediaLinks,
)
from app.services.linkedin import (
    find_linkedin_url,
    scrape_linkedin_profile,
    format_linkedin_profile,
    scrape_linkedin_company_page,
    format_linkedin_company,
)
from app.services.llm import invoke_llm
import json
from app.prompts.research import (
    DIGITAL_PRESENCE_PROMPT,
    INTERVIEW_SCRIPT_PROMPT,
    LEAD_PROFILE_PROMPT,
    LEAD_SCORING_PROMPT,
    OUTREACH_REPORT_PROMPT,
    PERSONALIZED_EMAIL_PROMPT,
)
from typing import Dict, Any
from app.services.scraper import analyse_website, scrape_website_to_markdown
from app.services.search.search import get_recent_news
from app.database import get_supabase_admin_client


async def fetch_linkedin_data(state: GraphState) -> GraphState:
    """Node: Fetch LinkedIn profile data."""

    print("📍 Node: fetch_linkedin_data")

    lead = state["current_lead"]
    updates = {
        "current_step": "linkedin_research",
        "completed_steps": ["linkedin_research"],
    }

    try:

        linkedin_url = lead.get("linkedin_url")

        if not linkedin_url and lead.get("name") and lead.get("company_name"):
            linkedin_url = await find_linkedin_url(
                name=lead["name"], company=lead["company_name"]
            )

        if not linkedin_url:
            updates["erros"] = ["Could not find LinkedIn URL."]
            updates["linkedin_profile"] = ["LinkedIn profile not found."]
            return updates

        profile_data = await scrape_linkedin_profile(linkedin_url)

        if "error" in profile_data:
            updates["errors"] = [profile_data["error"]]
            updates["linkedin_profile"] = ["Error fetching LinkedIn profile."]
            return updates

        formatted_profile = format_linkedin_profile(profile_data)

        profile_summary = invoke_llm(
            system_prompt=LEAD_PROFILE_PROMPT,
            user_message=formatted_profile,
        )

        updates["linkedin_profile"] = profile_summary

        updates["reports"] = [
            Report(
                report_type="LinkedIn Summary",
                title="LinkedIn Profile Analysis",
                content=profile_summary,
                is_markdown=True,
                metadata={"linkedin_url": linkedin_url},
            )
        ]

        company_linkedin = profile_data.get("company_linkedin_url", "")
        company_website = profile_data.get("company_website", "")

        if company_linkedin:
            company_data = await scrape_linkedin_company_page(company_linkedin)
            if "error" not in company_data:
                formatted_linkedin_company = format_linkedin_company(company_data)
                updates["company_data"] = CompanyInfo(
                    name=formatted_linkedin_company.get("name", ""),
                    profile=json.dumps(formatted_linkedin_company),
                    website=company_website
                    or formatted_linkedin_company.get("website", ""),
                    linkedin_url=company_linkedin,
                    social_media_links=SocialMediaLinks(),
                    raw_data=formatted_linkedin_company,
                )

    except Exception as e:
        updates["errors"] = [f"Exception during LinkedIn research: {str(e)}"]
        updates["linkedin_profile"] = ["Error during LinkedIn research."]

    return updates


async def analyse_company_website(state: GraphState) -> Dict[str, Any]:
    """Node: Analyze company website."""

    print("📍 Node: analyse_company_website")

    company = state.get("company_data", {})
    lead = state["current_lead"]

    updates = {
        "current_step": "website_analysis",
        "completed_steps": ["website_analysis"],
    }

    website_url = company.get("website") or lead.get("company_website", "")
    if not website_url:
        updates["website_analysis"] = ["No website URL available."]
        updates["errors"] = ["No company website to analyze"]
        return updates

    try:
        website_data = await analyse_website(website_url)
        updates["website_analysis"] = website_data.summary

        current_company = state.get("company_data", CompanyInfo())

        updates["company_data"] = CompanyInfo(
            name=current_company.get("name", ""),
            profile=current_company.get("profile", ""),
            website=website_url,
            linkedin_url=current_company.get("linkedin_url", ""),
            social_media_links=SocialMediaLinks(
                blog=website_data.blog_url,
                facebook=website_data.facebook,
                twitter=website_data.twitter,
                youtube=website_data.youtube,
            ),
            raw_data=current_company.get("raw_data", {}),
        )

        updates["reports"] = [
            Report(
                report_type="website_analysis",
                title="Website Analysis",
                content=website_data.summary,
                is_markdown=True,
                metadata={"website_url": website_url},
            )
        ]

    except Exception as e:
        updates["errors"] = [f"Website error: {str(e)}"]
        updates["website_analysis"] = f"Error: {str(e)}"

    return updates


async def analyse_blog_content(state: GraphState) -> Dict[str, Any]:
    """Node: Analyze social media presence."""

    print("📍 Node: analyse_blog_content")

    company = state.get("company_data", {})
    social_links = company.get("social_media_links", {})
    blog_url = social_links.get("blog", "")

    updates = {
        "completed_steps": ["blog_content_analysis"],
    }

    if not blog_url:
        updates["blog_analysis"] = "No blog URL found."
        return updates

    try:
        blog_content = await scrape_website_to_markdown(blog_url)
        company_name = company.get("name", "the company")

        print(blog_content)

        prompt = f"""
        Analyze the blog content for {company_name}.
        
        Evaluate:
        1. Publishing frequency
        2. Topics and relevance
        3. Content quality
        4. SEO indicators
        5. Improvement opportunities
        
        Provide a score out of 10.
        """

        blog_analysis = invoke_llm(
            system_prompt=prompt,
            user_message=blog_content,
        )

        updates["blog_analysis"] = blog_analysis

        updates["reports"] = [
            Report(
                report_type="blog_analysis",
                title="Blog Content Analysis",
                content=blog_analysis,
                is_markdown=True,
                metadata={"blog_url": blog_url},
            )
        ]

    except Exception as e:
        updates["errors"] = [f"Blog error: {str(e)}"]
        updates["blog_analysis"] = f"Error: {str(e)}"

    return updates


# Todo
async def analyze_social_media(state: GraphState) -> Dict[str, Any]:
    """Node: Analyze social media presence."""
    print("📍 Node: analyze_social_media")

    updates = {
        "completed_steps": ["social_media_analysis"],
    }

    company = state.get("company_data", {})
    social_links = company.get("social_media_links", {})

    # Build list of found profiles
    profiles = []
    for platform, url in social_links.items():
        if url and platform != "blog":  # Skip blog, we analyze it separately
            profiles.append(f"- **{platform.title()}**: {url}")

    if not profiles:
        updates["social_media_analysis"] = "No social media profiles found."
        return updates

    # Create a simple report of found profiles
    analysis = f"""
## Social Media Presence

Found profiles:
{chr(10).join(profiles)}


*Detailed analysis requires platform API access.*
"""

    updates["social_media_analysis"] = analysis
    updates["reports"] = [
        Report(
            report_type="social_media_analysis",
            title="Social Media Analysis",
            content=analysis,
            is_markdown=True,
            metadata={"social_links": social_links},
        )
    ]

    return updates


async def anayse_recent_news(state: GraphState) -> Dict[str, Any]:
    """Node: Gather recent news about the company."""
    print("📍 Node: anayse_recent_news")

    updates = {
        "completed_steps": ["news_analysis"],
    }

    company = state.get("company_data", {})
    company_name = company.get("name", "") or state["current_lead"].get(
        "company_name", ""
    )

    if not company_name:
        updates["news_analysis"] = "No company name for news search."
        return updates

    try:
        news = await get_recent_news(company_name, num_results=5)

        prompt = f"""
        Summarize recent news about {company_name}.
        
        Focus on:
        1. Major announcements
        2. Product launches
        3. Growth indicators
        4. Challenges
        5. Industry trends
        
        Highlight anything relevant for sales outreach.
        """

        if news or not news.startswith("No recent news"):
            analysis = invoke_llm(system_prompt=prompt, user_message=news)
        else:
            analysis = "No recent news found."

        updates["news_analysis"] = analysis
        updates["reports"] = [
            Report(
                report_type="news_analysis",
                title="Recent News Analysis",
                content=analysis,
                is_markdown=True,
                metadata={"company_name": company_name},
            )
        ]
    except Exception as e:
        updates["errors"] = [f"News error: {str(e)}"]
        updates["news_analysis"] = f"Error: {str(e)}"

    return updates


async def generate_digital_presence_report(
    state: GraphState,
) -> Dict[str, Any]:
    """Node: Generate digital presence report."""
    print("📍 Node: generate_digital_presence_report")

    updates = {
        "current_step": "digital_presence_report",
        "completed_steps": ["digital_presence_report"],
    }

    company = state.get("company_data", {})

    input_data = f"""
    # Company: {company.get('name', 'Unknown')}

    ## Website Analysis
    {state.get('website_analysis', 'Not available')}

    ## Blog Analysis
    {state.get('blog_analysis', 'Not available')}

    ## Social Media Analysis
    {state.get('social_media_analysis', 'Not available')}

    ## Recent News
    {state.get('news_analysis', 'Not available')}
    """
    report = invoke_llm(
        system_prompt=DIGITAL_PRESENCE_PROMPT,
        user_message=input_data,
    )

    updates["digital_presence_report"] = report
    updates["reports"] = [
        Report(
            report_type="digital_presence_report",
            title="Digital Presence Report",
            content=report,
            is_markdown=True,
            metadata={"company_name": company.get("name", "")},
        )
    ]

    return updates


async def generate_globa_research_report(state: GraphState) -> Dict[str, Any]:
    """Node: Generate final comprehensive research report."""
    print("📍 Node: generate_globa_research_report")

    updates = {
        "current_step": "global_research_report",
        "completed_steps": ["global_research_report"],
    }

    lead = state["current_lead"]
    company = state.get("company_data", {})

    input_data = f"""
    # Lead Profile
    **Name:** {lead.get('name', 'Unknown')}
    **Email:** {lead.get('email', 'Unknown')}
    **Company:** {lead.get('company_name', 'Unknown')}

    ## LinkedIn Profile
    {state.get("linkedin_profile", 'Not available')}

    ## Company Information
    {company.get('profile', 'Not available')}

    ## Digital Presence
    {state.get('digital_presence_report', 'Not available')}
    """

    prompt = """
    Create a Global Lead Research Report combining all research.

    Structure:
    1. Executive Summary
    2. Lead Profile Analysis
    3. Company Overview
    4. Digital Presence Evaluation
    5. Key Opportunities
    6. Recommended Approach
    """

    report = invoke_llm(
        system_prompt=prompt,
        user_message=input_data,
    )

    updates["global_research_report"] = report

    updates["reports"] = [
        Report(
            report_type="global_research",
            title="Global Lead Research Report",
            content=report,
            is_markdown=True,
            metadata={},
        )
    ]

    return updates


async def score_lead(state: GraphState) -> Dict[str, Any]:
    """Node: Score and qualify the lead."""
    print("📍 Node: score_lead")

    updates = {"current_step": "lead_scoring", "completed_steps": ["lead_scoring"]}

    research = state.get("global_research_report", "")

    if not research:

        research = f""" 

        Linkedin Profile: {state.get("linkedin_profile", "Not available")}
        Website Analysis: {state.get("website_analysis", "Not available")}
        Digital Presence Report: {state.get("digital_presence_report", "Not available")}

        """

    score_response = invoke_llm(
        system_prompt=LEAD_SCORING_PROMPT,
        user_message=research,
    )

    try:
        score_response = score_response.strip()

        # Remove markdown code blocks if present
        if "```" in score_response:
            score_response = score_response.split("```")[1]
            if score_response.startswith("json"):
                score_response = score_response[4:]
            score_response = score_response.strip()

        scores = json.loads(score_response)
    except json.JSONDecodeError:
        # Fallback if LLM doesn't return valid JSON
        scores = {
            "overall_score": 5.0,
            "qualification_status": "needs_review",
            "reasoning": "Could not parse response",
        }

    overall_score = scores.get("overall_score", 5.0)
    is_qualified = overall_score >= 6.0

    updates["lead_score"] = overall_score
    updates["score_detaisls"] = scores
    updates["is_qualified"] = is_qualified

    return updates


async def geenrate_outreach_report(state: GraphState) -> Dict[str, Any]:
    """Node: Generate personalized outreach report."""
    print("📍 Node: geenrate_outreach_report")
    updates = {
        "current_step": "outreach_report",
        "completed_steps": ["outreach_report"],
    }

    research = state.get("global_research_report", "")

    report = invoke_llm(
        system_prompt=OUTREACH_REPORT_PROMPT,
        user_message=research,
    )
    current_outreach = state.get("outreach_materials", OutreachMaterials())

    updates["outreach_materials"] = OutreachMaterials(
        report=report,
        email_subject=current_outreach.get("email_subject", ""),
        email_body=current_outreach.get("email_body", ""),
        interview_script=current_outreach.get("interview_script", ""),
    )

    updates["reports"] = [
        Report(
            report_type="outreach_report",
            title="Personalized Outreach Report",
            content=report,
            is_markdown=True,
            metadata={},
        )
    ]

    return updates


async def generate_personilized_email(state: GraphState) -> Dict[str, Any]:
    """Node: Generate personalized email."""

    print("📍 Node: generate_personilized_email")

    updates = {
        "completed_steps": ["email_generation"],
    }

    research = state.get("global_research_report", "")

    email_response = invoke_llm(
        system_prompt=PERSONALIZED_EMAIL_PROMPT,
        user_message=research,
    )

    try:
        email_response = email_response.strip()

        if "```" in email_response:
            email_response = email_response.split("```")[1]
            if email_response.startswith("json"):
                email_response = email_response[4:]

        email_data: Dict[str, Any] = json.loads(email_response)
        subject = email_data.get("subject", "")
        body = email_data.get("email", "")
    except json.JSONDecodeError:
        subject = "Quick Question"
        body = "Hi, I wanted to reach out regarding potential opportunities."

    current_outreach = state.get("outreach_materials", OutreachMaterials())

    updates["outreach_materials"] = OutreachMaterials(
        report=current_outreach.get("report", ""),
        email_subject=subject,
        email_body=body,
        interview_script=current_outreach.get("interview_script", ""),
    )

    return updates


async def generate_interview_script(state: GraphState) -> Dict[str, Any]:
    """Node: Generate personalized interview script."""
    print("📍 Node: generate_interview_script")

    updates = {
        "completed_steps": ["interview_script_generation"],
    }

    research = state.get("global_research_report", "")

    script = invoke_llm(
        system_prompt=INTERVIEW_SCRIPT_PROMPT,
        user_message=research,
    )

    current_outreach = state.get("outreach_materials", OutreachMaterials())

    updates["outreach_materials"] = OutreachMaterials(
        report=current_outreach.get("report", ""),
        email_subject=current_outreach.get("email_subject", ""),
        email_body=current_outreach.get("email_body", ""),
        interview_script=script,
    )

    updates["reports"] = [
        Report(
            report_type="interview_script",
            title="Personalized Interview Script",
            content=script,
            is_markdown=True,
            metadata={},
        )
    ]

    return updates


async def save_to_database(state: GraphState) -> Dict[str, Any]:
    """Node: Save all results to database."""
    print("📍 Node: save_to_database")

    updates = {"current_step": "saving", "completed_steps": ["saving"]}

    supabase = get_supabase_admin_client()

    lead_id = state["current_lead"]["id"]
    user_id = state["user_id"]

    try:
        status = "outreach_ready" if state.get("is_qualified") else "not_qualified"

        supabase.table("leads").update(
            {
                "status": status,
                "score": state.get("lead_score", 0),
                "score_details": state.get("score_details", {}),
            }
        ).eq("id", str(lead_id)).execute()

        company_data = state.get("company_data", {})
        if company_data:
            supabase.table("company_data").upsert(
                {
                    "lead_id": lead_id,
                    "name": company_data.get("name", ""),
                    "profile": company_data.get("profile", ""),
                    "website": company_data.get("website", ""),
                    "blog_url": company_data.get("social_media_links", {}).get(
                        "blog", ""
                    ),
                    "facebook_url": company_data.get("social_media_links", {}).get(
                        "facebook", ""
                    ),
                    "twitter_url": company_data.get("social_media_links", {}).get(
                        "twitter", ""
                    ),
                    "youtube_url": company_data.get("social_media_links", {}).get(
                        "youtube", ""
                    ),
                },
                on_conflict="lead_id",
            ).execute()
        for report in state.get("reports", []):
            supabase.table("reports").insert(
                {
                    "lead_id": lead_id,
                    "user_id": user_id,
                    "report_type": report["report_type"],
                    "title": report["title"],
                    "content": report["content"],
                    "is_markdown": report.get("is_markdown", True),
                    "metadata": report.get("metadata", {}),
                }
            ).execute()

        outreach = state.get("outreach_materials", {})

        if outreach.get("email_body"):
            supabase.table("outreach_materials").insert(
                {
                    "lead_id": lead_id,
                    "user_id": user_id,
                    "material_type": "email",
                    "subject": outreach.get("email_subject", ""),
                    "content": outreach.get("email_body", ""),
                }
            ).execute()

        if outreach.get("interview_script"):
            supabase.table("outreach_materials").insert(
                {
                    "lead_id": lead_id,
                    "user_id": user_id,
                    "material_type": "interview_script",
                    "content": outreach.get("interview_script", ""),
                }
            ).execute()
    except Exception as e:
        updates["errors"] = [f"Database error: {str(e)}"]

    return updates


def check_if_qualified(state: GraphState) -> str:
    """Route based on qualification status."""
    print("📍 Decision: check_if_qualified")
    if state.get("is_qualified", False):
        print("✅ Lead QUALIFIED - generating outreach")
        return "qualified"
    else:
        print("❌ Lead NOT QUALIFIED - skipping outreach")
        return "not_qualified"
