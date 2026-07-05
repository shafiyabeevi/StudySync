"""
Reference book/resource search service using Tavily API.
Searches for academic resources, textbooks, and reference materials.
"""
from tavily import TavilyClient
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

# Domains we prefer for academic results
TRUSTED_DOMAINS = [
    "springer.com", "wiley.com", "elsevier.com", "pearson.com",
    "oreilly.com", "cambridge.org", "oxford.org", "mit.edu",
    "stanford.edu", "archive.org", "scholar.google.com",
    "coursera.org", "edx.org", "khanacademy.org",
    "geeksforgeeks.org", "tutorialspoint.com",
    "amazon.com", "goodreads.com",
]

# Domains to exclude (piracy, low quality)
EXCLUDED_KEYWORDS = ["freepdf", "pirate", "torrent", "libgen", "z-lib"]


def _get_tavily_client() -> TavilyClient:
    settings = get_settings()
    return TavilyClient(api_key=settings.TAVILY_API_KEY)


async def search_references(topic: str) -> list[dict]:
    """
    Search for reference books and academic resources on a topic.
    Returns a list of dicts with title, description, url, source_type.
    """
    client = _get_tavily_client()

    # Build an academic-focused query
    query = f"best textbook reference book for {topic} academic resource"

    try:
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=10,
            include_answer=False,
        )

        results = []
        seen_urls = set()

        for item in response.get("results", []):
            url = item.get("url", "")
            title = item.get("title", "")

            # Skip duplicates
            if url in seen_urls:
                continue

            # Skip known piracy sites
            if any(kw in url.lower() for kw in EXCLUDED_KEYWORDS):
                continue

            # Determine source type
            source_type = _classify_source(url)

            results.append({
                "title": title,
                "description": item.get("content", "")[:300],  # Truncate long snippets
                "url": url,
                "source_type": source_type,
            })
            seen_urls.add(url)

        logger.info(f"Found {len(results)} references for topic: {topic}")
        return results

    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        raise ValueError(f"Reference search failed: {str(e)}")


def _classify_source(url: str) -> str:
    """Classify a URL into a source type for display purposes."""
    lower = url.lower()
    if any(d in lower for d in ["amazon.com", "goodreads.com", "springer.com", "wiley.com",
                                 "elsevier.com", "pearson.com", "oreilly.com", "cambridge.org"]):
        return "book"
    elif any(d in lower for d in [".edu", "scholar.google"]):
        return "academic"
    elif any(d in lower for d in ["coursera.org", "edx.org", "khanacademy.org", "udemy.com"]):
        return "course"
    elif any(d in lower for d in ["youtube.com", "youtu.be"]):
        return "video"
    elif any(d in lower for d in ["geeksforgeeks.org", "tutorialspoint.com", "w3schools.com"]):
        return "tutorial"
    else:
        return "web"
