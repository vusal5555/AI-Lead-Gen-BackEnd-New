import re
import httpx
import html2text
from bs4 import BeautifulSoup
from pydantic import BaseModel

from app.services.llm import invoke_llm


class WebsiteData(BaseModel):
    """Structured data extracted from a website."""

    summary: str
    blog_url: str = ""
    youtube: str = ""
    twitter: str = ""
    facebook: str = ""


async def scrape_website_to_markdown(url: str) -> str:
    """
    Scrape a website and convert its content to markdown.

    Args:
        url: The URL to scrape

    Returns:
        Markdown formatted content of the page
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        # Return error message instead of raising (so workflow continues)
        return f"Error: Could not fetch {url} - HTTP {e.response.status_code}"
    except httpx.TimeoutException:
        return f"Error: Timeout fetching {url}"
    except Exception as e:
        return f"Error: {str(e)}"

    soup = BeautifulSoup(response.text, "html.parser")

    for script in soup(["script", "style", "noscript"]):
        script.decompose()

    html_content = soup.prettify()

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_tables = True
    markdown_content = h.handle(html_content)

    # Clean up excess newlines
    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
    markdown_content = markdown_content.strip()

    # Limit content length to avoid token limits
    if len(markdown_content) > 15000:
        markdown_content = markdown_content[:15000] + "\n\n[Content truncated...]"

    return markdown_content


async def analyse_website(url: str) -> WebsiteData:
    """
    Scrape and analyze a website to extract key information.

    Args:
        url: The company website URL

    Returns:
        WebsiteData with summary and social media links
    """

    website_content = await scrape_website_to_markdown(url)

    if website_content.startswith("Error"):
        return WebsiteData(
            summary=f"Could not analyze website: {website_content}",
            blog_url="",
            youtube="",
            twitter="",
            facebook="",
        )

    system_prompt = f"""
    The provided webpage content is scraped from: {url}

    # Tasks

    ## 1- Summarize webpage content:
    Write a 300 word comprehensive summary about the content of the webpage. 
    Focus on relevant information related to company mission, products and services.

    ## 2- Extract and categorize the following links:
    1. Blog URL: Extract the main blog URL of the company. 
    2. Social Media Links: Extract links to the company's YouTube, Twitter, and Facebook profiles.
    
    If a link is not found, return an empty string for that field.
    If the link is relative (e.g., "/blog"), prepend it with {url} to form an absolute URL.
    """

    result = invoke_llm(
        system_prompt=system_prompt,
        user_message=website_content,
        response_format=WebsiteData,
    )
    return result
