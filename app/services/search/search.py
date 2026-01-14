import httpx
from typing import List, Dict, Any

from app.config import get_settings


async def google_search(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Perform a Google search using Serper API.

    Args:
        query: Search query
        num_results: Number of results to return

    Returns:
        List of search results with title, link, and snippet

    """

    settings = get_settings()

    api_key = settings.serper_api_key

    if not api_key:
        raise ValueError("Serper API key not configured.")

    url = "https://google.serper.dev/search"

    headers = {"X-API-KEY": settings.serper_api_key, "Content-Type": "application/json"}

    params = {"q": query, "num": num_results}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url, headers=headers, json=params, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("organic", [])
        except httpx.HTTPError as e:
            raise RuntimeError(f"Google search failed: {e}")


def days_back_to_tbs(days_back: int) -> str:
    """
    Convert a days_back value into Serper/Google 'tbs' quick-date-range filters.
    qdr:d = day, qdr:w = week, qdr:m = month, qdr:y = year
    """

    if days_back <= 1:
        return "qdr:d"
    if days_back <= 7:
        return "qdr:w"
    if days_back <= 31:
        return "qdr:m"
    return "qdr:y"


async def get_recent_news(
    company: str, num_results: int = 5, days_back: int = 30
) -> List[Dict[str, Any]]:
    """
    Get recent news about a company using Serper API.

    Args:
        company: Company name to search for
        num_results: Number of news results
        days_back: Recency window. Mapped to Serper's qdr filters (day/week/month/year).
    Returns:
        Formatted string of recent news
    """

    settings = get_settings()

    api_key = settings.serper_api_key

    if not api_key:
        raise ValueError("Serper API key not configured.")

    url = "https://google.serper.dev/news"

    headers = {"X-API-KEY": settings.serper_api_key, "Content-Type": "application/json"}

    tbs = days_back_to_tbs(days_back)
    params = {"q": company, "num": num_results, "tbs": tbs}  # Last month

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url, headers=headers, json=params, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            news_items = data.get("news", [])
        except httpx.HTTPError as e:
            raise RuntimeError(f"News search failed: {e}")

    if not news_items:
        return "No recent news found."

    news_list = []
    for item in news_items:
        item: Dict[str, Any] = item
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        date = item.get("date", "")
        link = item.get("link", "")
        news_list.append(f"**{title}**\n{snippet}\nDate: {date}\nURL: {link}\n")

    return "\n".join(news_list)
