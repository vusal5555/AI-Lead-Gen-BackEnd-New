import re
import httpx
import html2text
from bs4 import BeautifulSoup
from pydantic import BaseModel
from urllib.parse import urljoin
from app.services.llm import invoke_llm


class WebsiteData(BaseModel):
    """Structured data extracted from a website."""

    summary: str
    blog_url: str = ""
    youtube: str = ""
    twitter: str = ""
    facebook: str = ""


def extract_important_links(html_content: str, base_url: str) -> dict:
    """
    Extract blog and social media links directly from HTML.
    This runs BEFORE truncation so we don't lose footer links.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    links = {
        "blog_url": "",
        "youtube": "",
        "twitter": "",
        "facebook": "",
        "instagram": "",
        "linkedin": "",
    }

    # Blog patterns (in href or link text)
    blog_patterns = ["/blog", "/news", "/articles", "/insights", "/resources", "/posts"]
    blog_text_patterns = ["blog", "news", "articles", "insights"]

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").lower()
        text = anchor.get_text().lower().strip()
        full_url = urljoin(base_url, anchor.get("href", ""))

        # Blog URL
        if not links["blog_url"]:
            for pattern in blog_patterns:
                if pattern in href:
                    links["blog_url"] = full_url
                    break
            if not links["blog_url"]:
                for pattern in blog_text_patterns:
                    if pattern in text and len(text) < 20:  # Short link text
                        links["blog_url"] = full_url
                        break

        # Social media
        if "youtube.com" in href or "youtu.be" in href:
            links["youtube"] = full_url
        elif "twitter.com" in href or "x.com" in href:
            links["twitter"] = full_url
        elif "facebook.com" in href or "fb.com" in href:
            links["facebook"] = full_url
        elif "instagram.com" in href:
            links["instagram"] = full_url
        elif "linkedin.com" in href:
            links["linkedin"] = full_url

    return links


async def scrape_website_to_markdown(url: str) -> tuple[str, dict]:
    """
    Scrape a website and convert its content to markdown.
    Also extracts important links BEFORE truncation.

    Returns:
        Tuple of (markdown_content, extracted_links)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        return f"Error: Could not fetch {url} - HTTP {e.response.status_code}", {}
    except httpx.TimeoutException:
        return f"Error: Timeout fetching {url}", {}
    except Exception as e:
        return f"Error: {str(e)}", {}

    raw_html = response.text

    # Extract links BEFORE any processing
    extracted_links = extract_important_links(raw_html, url)

    soup = BeautifulSoup(raw_html, "html.parser")

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

    return markdown_content, extracted_links


async def analyse_website(url: str) -> WebsiteData:
    """
    Scrape and analyze a website to extract key information.

    Args:
        url: The company website URL

    Returns:
        WebsiteData with summary and social media links
    """

    website_content, extracted_links = await scrape_website_to_markdown(url)

    if website_content.startswith("Error"):
        return WebsiteData(
            summary=f"Could not analyze website: {website_content}",
            blog_url=extracted_links.get("blog_url", ""),
            youtube=extracted_links.get("youtube", ""),
            twitter=extracted_links.get("twitter", ""),
            facebook=extracted_links.get("facebook", ""),
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

    if not result.blog_url and extracted_links.get("blog_url"):
        result.blog_url = extracted_links["blog_url"]
    if not result.youtube and extracted_links.get("youtube"):
        result.youtube = extracted_links["youtube"]
    if not result.twitter and extracted_links.get("twitter"):
        result.twitter = extracted_links["twitter"]
    if not result.facebook and extracted_links.get("facebook"):
        result.facebook = extracted_links["facebook"]
    return result
