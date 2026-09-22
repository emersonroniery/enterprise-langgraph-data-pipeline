"""Web extraction engine supporting both headless browser automation and fast async HTTP requests.

Leverages Playwright for dynamic SPA rendering and HTTPX/BeautifulSoup for high-throughput static extraction.
"""

from typing import Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Playwright
from src.config import settings
from src.utils.logger import logger


class AsyncScraper:
    """Enterprise asynchronous data scraper with hybrid execution strategy."""

    def __init__(self, timeout: float = 30.0) -> None:
        """Initializes the scraper with timeout and browser session parameters."""
        self.timeout = timeout
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    async def __aenter__(self) -> "AsyncScraper":
        """Async context manager entry: initializes Playwright browser instance."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.HEADLESS_BROWSER
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit: gracefully disposes browser resources."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def fetch_static(self, url: str) -> Dict[str, Any]:
        """Fetches static web pages using HTTPX and parses DOM via BeautifulSoup.

        Args:
            url: Target web page URL.

        Returns:
            Extracted document dictionary with status, title, and raw HTML.
        """
        logger.info("Executing static HTTP extraction: {}", url)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string.strip() if soup.title and soup.title.string else ""

            return {
                "url": url,
                "status": response.status_code,
                "title": title,
                "html": response.text,
            }

    async def fetch_dynamic(self, url: str, wait_selector: Optional[str] = None) -> Dict[str, Any]:
        """Renders dynamic JavaScript-heavy pages using headless Playwright.

        Args:
            url: Target web page URL.
            wait_selector: Optional CSS selector to wait for before extracting DOM.

        Returns:
            Extracted document dictionary with rendered HTML and page metadata.
        """
        logger.info("Executing dynamic browser extraction: {}", url)
        if not self._browser:
            raise RuntimeError("Browser not initialized. Use 'async with AsyncScraper():' context.")

        page = await self._browser.new_page()
        try:
            await page.goto(url, timeout=int(self.timeout * 1000))
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=int(self.timeout * 1000))

            content = await page.content()
            title = await page.title()

            return {
                "url": url,
                "status": 200,
                "title": title,
                "html": content,
            }
        finally:
            await page.close()
