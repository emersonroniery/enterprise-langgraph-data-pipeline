"""Unit and integration tests for data extraction mechanisms."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.extractors.scraper import AsyncScraper


@pytest.mark.asyncio
async def test_fetch_static_success():
    """Validates that static extraction correctly parses HTML titles and payloads."""
    mock_html = "<html><head><title>Test Page</title></head><body><h1>Hello</h1></body></html>"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        scraper = AsyncScraper()
        result = await scraper.fetch_static("https://example.com")

        assert result["status"] == 200
        assert result["title"] == "Test Page"
        assert "Hello" in result["html"]
        mock_get.assert_awaited_once_with("https://example.com")


@pytest.mark.asyncio
async def test_fetch_dynamic_without_context_raises_runtime_error():
    """Ensures dynamic browser extraction raises error if context manager is uninitialized."""
    scraper = AsyncScraper()
    with pytest.raises(RuntimeError, match="Browser not initialized"):
        await scraper.fetch_dynamic("https://example.com")
