"""Web Search Tool — Real DuckDuckGo Search
Searches the web for information using DuckDuckGo (no API key needed).
"""
from __future__ import annotations

import json
from typing import Any

import httpx


class WebSearch:
    """Web search tool — uses DuckDuckGo (free, no API key)"""

    def __init__(self, search_url: str | None = None, api_key: str | None = None):
        self.search_url = search_url or "https://api.duckduckgo.com"
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search the web using DuckDuckGo Instant Answer API

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of dicts with keys: title, url, snippet
        """
        client = await self._get_client()
        try:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1,
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []
            # Parse Abstract
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", "Summary"),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data["AbstractText"],
                })

            # Parse Related Topics
            for topic in data.get("RelatedTopics", []):
                if len(results) >= max_results:
                    break
                if "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "").split(" - ")[0],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                    })
                elif "Topics" in topic:
                    for sub in topic["Topics"]:
                        if len(results) >= max_results:
                            break
                        results.append({
                            "title": sub.get("Text", "").split(" - ")[0],
                            "url": sub.get("FirstURL", ""),
                            "snippet": sub.get("Text", ""),
                        })

            return results[:max_results]

        except Exception:
            # Fallback: try DuckDuckGo HTML scrape (lite version)
            return await self._search_lite(query, max_results)

    async def _search_lite(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Fallback: scrape DuckDuckGo lite HTML"""
        client = await self._get_client()
        try:
            response = await client.post(
                "https://lite.duckduckgo.com/lite/",
                data={"q": query},
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; JnusBot/1.0)",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            response.raise_for_status()
            # Simple HTML parsing for results
            from html.parser import HTMLParser

            class ResultParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.results = []
                    self._in_result = False
                    self._current = {}
                    self._tag_stack = []

                def handle_starttag(self, tag, attrs):
                    self._tag_stack.append(tag)
                    attrs_dict = dict(attrs)
                    if tag == "a" and "result-link" in attrs_dict.get("class", ""):
                        self._in_result = True
                        self._current = {"title": "", "url": attrs_dict.get("href", ""), "snippet": ""}

                def handle_data(self, data):
                    if self._in_result:
                        self._current["title"] += data.strip()

                def handle_endtag(self, tag):
                    if tag == "a" and self._in_result:
                        self._in_result = False
                        if self._current.get("title"):
                            self.results.append(self._current)
                        self._current = {}
                    if self._tag_stack:
                        self._tag_stack.pop()

            parser = ResultParser()
            parser.feed(response.text)
            return parser.results[:max_results]

        except Exception:
            # Ultimate fallback: return empty list
            return []

    async def fetch_page(self, url: str) -> str | None:
        """Fetch and return the text content of a URL

        Args:
            url: The URL to fetch

        Returns:
            Page text content or None if failed
        """
        client = await self._get_client()
        try:
            response = await client.get(url, follow_redirects=True, timeout=20.0)
            response.raise_for_status()
            # Return plain text (strip HTML tags)
            import re
            text = re.sub(r"<[^>]+>", " ", response.text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:5000]  # Limit to 5000 chars
        except Exception:
            return None

    async def search_and_summarize(self, query: str) -> dict[str, Any]:
        """Search and return a summary of results"""
        results = await self.search(query)
        return {
            "query": query,
            "result_count": len(results),
            "results": results,
            "summary": f"Found {len(results)} results for '{query}'",
        }

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
