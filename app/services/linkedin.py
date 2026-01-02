import httpx
from typing import Optional, Tuple, Dict, Any

from app.config import get_settings
from app.services.llm import invoke_llm
from app.services.search.search import google_search


async def find_linkedin_url(name: str, company: str) -> Optional[str]:
    """
    Find a person's LinkedIn URL by searching Google.

    Args:
        name: Person's full name
        company: Company name they work at

    Returns:
        LinkedIn URL if found, None otherwise
    """

    query = f'site:linkedin.com/in "{name}" "{company}"'

    results = await google_search(query=query)

    for result in results:
        result: Dict[str, Any] = result
        url = result.get("link", "")
        if "linkedin.com/in/" in url:
            return url

    return None


async def scrape_linkedin_profile(url: str) -> Dict[str, Any]:
    """
    Scrape a LinkedIn profile using RapidAPI.

    Args:
        linkedin_url: The LinkedIn profile URL

    Returns:
        Dictionary containing profile data
    """

    settings = get_settings()
    api_url = f"https://fresh-linkedin-profile-data.p.rapidapi.com/enrich-lead?linkedin_url={url}"

    if not settings.rapidapi_key:
        return {"error": "RapidAPI key not configured."}

    headers = {
        "x-rapidapi-key": settings.rapidapi_key,
        "x-rapidapi-host": "fresh-linkedin-profile-data.p.rapidapi.com",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(api_url, headers=headers)
            print(response)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data.get("data", {})
        except httpx.HTTPError as e:
            return {"error": f"Failed to scrape LinkedIn: {str(e)}"}


async def scrape_linkedin_company_page(url: str) -> Dict[str, Any]:
    """
    Scrape a LinkedIn company page using RapidAPI.

    Args:
        linkedin_url: The LinkedIn company URL

    Returns:
        Dictionary containing company data
    """

    settings = get_settings()

    api_url = f"https://fresh-linkedin-profile-data.p.rapidapi.com/enrich-lead?linkedin_url={url}"

    if not settings.rapidapi_key:
        return {"error": "RapidAPI key not configured."}

    headers = {
        "x-rapidapi-key": settings.rapidapi_key,
        "x-rapidapi-host": "fresh-linkedin-profile-data.p.rapidapi.com",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(api_url, headers=headers)
            response.raise_for_status()
            data: Dict[str, Any] = response.json()
            return data.get("data", {})
        except httpx.HTTPError as e:
            return {"error": f"Failed to scrape LinkedIn Company Page: {str(e)}"}


def format_linkedin_profile(raw_data: dict[str, Any]) -> str:
    """
    Format raw LinkedIn profile data into a readable summary.

    Args:
        profile_data: Raw data from LinkedIn scraper

    Returns:
        Formatted profile summary
    """
    if "error" in raw_data:
        return f"Error retrieving LinkedIn profile: {raw_data['error']}"

    profile = {
        "name": raw_data.get("full_name", "Unknown"),
        "headline": raw_data.get("headline", ""),
        "location": raw_data.get("location", ""),
        "about": raw_data.get("about", ""),
        "current_company": raw_data.get("company", ""),
        "current_title": raw_data.get("job_title", ""),
        "experiences": raw_data.get("experiences", []),
        "educations": raw_data.get("educations", []),
        "skills": raw_data.get("skills", []),
    }

    summary_parts = [
        f"# {profile['name']}",
        f"**{profile['headline']}**" if profile["headline"] else "",
        f"📍 {profile['location']}" if profile["location"] else "",
        "",
        "## About",
        profile["about"] if profile["about"] else "No about section available.",
        "",
        "## Current Position",
        (
            f"**{profile['current_title']}** at **{profile['current_company']}**"
            if profile["current_company"]
            else "Not specified"
        ),
        "",
        "## Experience",
    ]

    for exp in profile["experiences"]:
        exp: Dict[str, Any] = exp
        company = exp.get("company", "Unknown Company")
        title = exp.get("title", "Unknown")
        date_range = exp.get("date_range", "")
        summary_parts.append(f"- **{title}** at {company} ({date_range})")

    for edu in profile["educations"][:3]:
        edu: Dict[str, Any] = edu
        school = edu.get("school", "Unknown")
        degree = edu.get("degree", "")
        field = edu.get("field_of_study", "")
        summary_parts.append(f"- {degree} {field} - {school}")

    # Add skills
    if profile["skills"]:
        summary_parts.extend(["", "## Skills"])
        skills_str = ", ".join(profile["skills"][:10])
        summary_parts.append(skills_str)

    return "\n".join(summary_parts)


def format_linkedin_company(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format raw LinkedIn company data into a structured format.

    Args:
        company_data: Raw data from LinkedIn scraper

    Returns:
        Formatted company information
    """
    if "error" in company_data:
        return {"error": company_data["error"]}

    return {
        "name": company_data.get("company_name", ""),
        "description": company_data.get("description", ""),
        "website": company_data.get("website", ""),
        "industry": company_data.get("industries", []),
        "company_size": company_data.get("employee_count", ""),
        "headquarters": company_data.get("locations", []),
        "founded": company_data.get("year_founded", ""),
        "specialties": company_data.get("specialties", ""),
        "linkedin_url": company_data.get("linkedin_url", ""),
    }
