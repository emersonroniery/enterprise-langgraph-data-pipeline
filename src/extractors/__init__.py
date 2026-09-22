"""Data extraction subsystem package.

Integrates headless browser scraping (Playwright) and fast asynchronous HTTP fetching (HTTPX).
"""

from src.extractors.scraper import AsyncScraper

__all__ = ["AsyncScraper"]
