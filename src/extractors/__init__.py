"""Data extraction subsystem package.

Integrates resilient asynchronous web extraction via HTTPX and BeautifulSoup.
"""

from src.extractors.scraper import WebExtractor

__all__ = ["WebExtractor"]
