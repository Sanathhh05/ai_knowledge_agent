"""
Web page text extraction service.

Uses httpx for fetching and BeautifulSoup for HTML parsing.
Strips scripts, styles, and navigation elements to extract readable text.
"""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

# Tags to remove entirely (they contain no useful text)
_REMOVE_TAGS = {
    "script", "style", "nav", "header", "footer", "aside",
    "form", "iframe", "noscript", "svg", "figure",
}

# Maximum response size (5 MB)
_MAX_CONTENT_LENGTH = 5 * 1024 * 1024

# Request timeout (seconds)
_TIMEOUT = 30


def extract_text_from_url(url: str) -> dict:
    """
    Fetch a web page and extract its readable text content.

    Args:
        url: The web page URL.

    Returns:
        dict with keys:
          - text: extracted readable text
          - title: page title from <title> tag
          - url: the fetched URL

    Raises:
        ValueError: If the URL is unreachable, returns an error, or has no text.
    """
    try:
        response = httpx.get(
            str(url),
            timeout=_TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; AIKnowledgeAssistant/1.0; "
                    "+https://github.com/ai-knowledge-assistant)"
                )
            },
        )
        response.raise_for_status()
    except httpx.TimeoutException:
        raise ValueError(f"Request to {url} timed out after {_TIMEOUT} seconds.")
    except httpx.HTTPStatusError as e:
        raise ValueError(f"HTTP {e.response.status_code} error fetching {url}.")
    except httpx.RequestError as e:
        raise ValueError(f"Failed to fetch {url}: {str(e)}")

    # Check content length
    if len(response.content) > _MAX_CONTENT_LENGTH:
        raise ValueError(f"Page content exceeds {_MAX_CONTENT_LENGTH // (1024*1024)} MB limit.")

    # Check content type
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "text/plain" not in content_type:
        raise ValueError(
            f"Unsupported content type: {content_type}. "
            "Only HTML and plain text pages are supported."
        )

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else str(url)

    # Remove unwanted elements
    for tag_name in _REMOVE_TAGS:
        for element in soup.find_all(tag_name):
            element.decompose()

    # Extract text
    text = soup.get_text(separator="\n", strip=True)

    if not text.strip():
        raise ValueError(f"No readable text content found at {url}.")

    return {
        "text": text,
        "title": title,
        "url": str(url),
    }
