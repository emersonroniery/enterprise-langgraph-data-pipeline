"""Asynchronous web data extraction module with structured resilience and fallback strategies.

Fetches target websites, parses semantic DOM trees, and extracts structured text
and metadata for market intelligence analysis.
"""

import time
from typing import Any, Dict, List, Optional
import httpx
from bs4 import BeautifulSoup
from src.config import settings
from src.utils.logger import logger


class WebExtractor:
    """Enterprise asynchronous web extractor leveraging HTTPX and BeautifulSoup."""

    def __init__(
        self,
        timeout: Optional[float] = None,
        max_redirects: int = 5,
    ) -> None:
        """Initializes extractor with configurable timeout and network boundaries."""
        self.timeout = timeout or settings.REQUEST_TIMEOUT
        self.max_redirects = max_redirects
        self.default_headers = {
            "User-Agent": settings.DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def extract(self, url: str, attempt: int = 0) -> Dict[str, Any]:
        """Asynchronously extracts DOM text, headers, and metadata from a target URL.

        Implements an automatic structured fallback strategy when initial requests
        encounter network timeouts, client barriers, or HTTP errors.

        Args:
            url: The target endpoint to fetch and extract.
            attempt: Current retry attempt count.

        Returns:
            Dictionary containing raw extraction payload and diagnostic metrics.
        """
        logger.info("Starting web extraction for URL: {} (attempt {})", url, attempt)
        start_time = time.perf_counter()

        # Primary extraction attempt
        try:
            return await self._fetch_and_parse(url, headers=self.default_headers, start_time=start_time)
        except Exception as primary_exc:
            logger.warning(
                "Primary extraction failed for {} ({}). Initiating structured fallback...",
                url,
                primary_exc,
            )
            return await self._execute_fallback(url, attempt=attempt, original_error=primary_exc, start_time=start_time)

    async def _fetch_and_parse(
        self,
        url: str,
        headers: Dict[str, str],
        start_time: float,
    ) -> Dict[str, Any]:
        """Executes the HTTP GET request and parses semantic DOM structure."""
        async with httpx.AsyncClient(
            headers=headers,
            timeout=self.timeout,
            follow_redirects=True,
            max_redirects=self.max_redirects,
            verify=True,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            parsed_dom = self._parse_html(response.text)

            return {
                "url": str(response.url),
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
                "is_fallback": False,
                "headers": dict(response.headers),
                **parsed_dom,
            }

    async def _execute_fallback(
        self,
        url: str,
        attempt: int,
        original_error: Exception,
        start_time: float,
    ) -> Dict[str, Any]:
        """Structured fallback mechanism: tries alternate minimal headers and relaxed TLS."""
        fallback_headers = {
            "User-Agent": f"Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html) fallback-attempt-{attempt}",
            "Accept": "*/*",
        }

        try:
            async with httpx.AsyncClient(
                headers=fallback_headers,
                timeout=self.timeout + 5.0,
                follow_redirects=True,
                verify=False,
            ) as client:
                response = await client.get(url)
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

                if response.status_code < 400:
                    parsed_dom = self._parse_html(response.text)
                    logger.info("Structured fallback succeeded for: {}", url)
                    return {
                        "url": str(response.url),
                        "status_code": response.status_code,
                        "elapsed_ms": elapsed_ms,
                        "is_fallback": True,
                        "fallback_notes": f"Recovered from primary failure: {original_error}",
                        "headers": dict(response.headers),
                        **parsed_dom,
                    }
        except Exception as fallback_exc:
            logger.error("Fallback extraction also failed for {}: {}", url, fallback_exc)

        # Graceful diagnostic degradation when both strategies encounter errors
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "url": url,
            "status_code": getattr(getattr(original_error, "response", None), "status_code", 500),
            "elapsed_ms": elapsed_ms,
            "is_fallback": True,
            "error": str(original_error),
            "title": "",
            "meta_description": "",
            "headings": [],
            "paragraphs": [],
            "raw_text": "",
            "word_count": 0,
        }

    def _parse_html(self, html_content: str) -> Dict[str, Any]:
        """Parses HTML document and extracts structural elements."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Strip scripts, styles, and SVG artifacts
        for element in soup(["script", "style", "svg", "noscript", "iframe"]):
            element.decompose()

        # Extract title and meta description
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        meta_tag = (
            soup.find("meta", attrs={"name": "description"})
            or soup.find("meta", attrs={"property": "og:description"})
        )
        meta_description = meta_tag["content"].strip() if meta_tag and "content" in meta_tag.attrs else ""

        # Extract structural headings (H1 - H3)
        headings: List[Dict[str, str]] = []
        for tag_name in ["h1", "h2", "h3"]:
            for header in soup.find_all(tag_name):
                text = header.get_text(strip=True)
                if text:
                    headings.append({"level": tag_name.upper(), "text": text})

        # Extract readable text paragraphs
        paragraphs = [
            p.get_text(strip=True)
            for p in soup.find_all(["p", "article", "section"])
            if p.get_text(strip=True)
        ]

        full_text = " ".join(paragraphs)
        words = full_text.split()

        return {
            "title": title,
            "meta_description": meta_description,
            "headings": headings[:15],
            "paragraphs": paragraphs[:25],
            "raw_text": full_text[:10000],
            "word_count": len(words),
        }
