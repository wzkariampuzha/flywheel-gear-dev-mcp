"""Documentation fetcher with async HTTP and caching."""

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx
import yaml

from . import parsers

logger = logging.getLogger(__name__)

# Global cache for documentation
_docs_cache: dict[str, dict[str, Any]] = {}


async def fetch_all_docs(config_path: str = "config.yaml") -> dict[str, dict[str, Any]]:
    """Fetch all documentation sources defined in config file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Dictionary mapping tool_name to doc metadata:
        {
            'tool_name': {
                'content': 'markdown content...',
                'display_name': 'Display Name',
                'description': 'Description',
                'urls': ['https://...'],
                'fetched_at': datetime,
                'size': 12345
            }
        }
    """
    global _docs_cache

    # Load configuration
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    sources = config.get("documentation_sources", [])
    logger.info(f"Fetching {len(sources)} documentation sources...")

    # Fetch all sources in parallel
    tasks = [_fetch_source(source) for source in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build cache
    _docs_cache = {}
    for source, result in zip(sources, results):
        tool_name = source["tool_name"]

        if isinstance(result, Exception):
            logger.error(f"Failed to fetch {tool_name}: {result}")
            _docs_cache[tool_name] = {
                "content": f"# Error\n\nFailed to fetch documentation: {result}",
                "display_name": source.get("display_name", tool_name),
                "description": source.get("description", ""),
                "urls": source.get("urls", []),
                "fetched_at": datetime.now(),
                "size": 0,
                "error": str(result),
            }
        else:
            _docs_cache[tool_name] = result

    logger.info(f"Successfully cached {len(_docs_cache)} documentation sources")
    return _docs_cache


async def _fetch_source(source: dict[str, Any]) -> dict[str, Any]:
    """Fetch a single documentation source.

    Args:
        source: Source configuration from YAML

    Returns:
        Documentation metadata dict
    """
    tool_name = source["tool_name"]
    urls = source.get("urls", [])
    doc_type = source.get("type", "html")
    strip_deprecated = source.get("strip_deprecated", True)
    filter_sections = source.get("filter_sections")

    logger.info(f"Fetching {tool_name} from {len(urls)} URL(s)...")

    # Fetch all URLs for this source
    contents = []
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for url in urls:
            content = await _fetch_with_retry(client, url)
            if content:
                contents.append(content)

    if not contents:
        raise ValueError(f"No content fetched for {tool_name}")

    # Parse based on type
    parsed_contents = []
    for content in contents:
        if doc_type == "html":
            parsed = parsers.parse_html(content, urls[0], strip_deprecated)
        elif doc_type == "xml":
            parsed = parsers.parse_xml(content, filter_sections)
        elif doc_type == "json":
            parsed = parsers.parse_json_schema(content)
        elif doc_type == "gitlab_repo":
            parsed = parsers.parse_gitlab_repo(content, strip_deprecated)
        else:
            parsed = content  # Unknown type, store as-is

        parsed_contents.append(parsed)

    # Combine all contents
    combined_content = "\n\n---\n\n".join(parsed_contents)

    return {
        "content": combined_content,
        "display_name": source.get("display_name", tool_name),
        "description": source.get("description", ""),
        "urls": urls,
        "fetched_at": datetime.now(),
        "size": len(combined_content),
    }


async def _fetch_with_retry(
    client: httpx.AsyncClient, url: str, max_retries: int = 3
) -> str | None:
    """Fetch URL with exponential backoff retry.

    Args:
        client: httpx AsyncClient
        url: URL to fetch
        max_retries: Maximum number of retry attempts

    Returns:
        Content as string, or None if all retries failed
    """
    for attempt in range(max_retries):
        try:
            logger.debug(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
            response = await client.get(url)
            response.raise_for_status()
            return response.text

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code} for {url}")
            if e.response.status_code in [404, 403, 401]:
                # Don't retry client errors
                return None
            # Retry server errors
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)  # Exponential backoff
            else:
                raise

        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning(f"Request error for {url}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)
            else:
                raise

    return None


def get_cached_doc(tool_name: str) -> dict[str, Any] | None:
    """Get cached documentation for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Documentation metadata dict, or None if not found
    """
    return _docs_cache.get(tool_name)


def get_all_cached_docs() -> dict[str, dict[str, Any]]:
    """Get all cached documentation.

    Returns:
        Complete cache dictionary
    """
    return _docs_cache.copy()
