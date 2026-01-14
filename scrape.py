import asyncio
from app.services.scraper import scrape_website_to_markdown


async def test():
    url = "https://www.rb2b.com"
    content, links = await scrape_website_to_markdown(url)  # Unpack tuple

    print("=" * 60)
    print("EXTRACTED LINKS")
    print("=" * 60)
    for key, value in links.items():
        print(f"  {key}: {value}")

    print("=" * 60)
    print("SCRAPED CONTENT (first 2000 chars)")
    print("=" * 60)
    print(content[:2000])

    print("=" * 60)
    # Search for blog-related keywords
    blog_keywords = ["blog", "news", "article", "insight", "resource", "post"]
    for keyword in blog_keywords:
        if keyword in content.lower():
            print(f"✅ Found '{keyword}' in content")
        else:
            print(f"❌ '{keyword}' not found")


asyncio.run(test())
