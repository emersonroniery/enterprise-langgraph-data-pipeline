"""Unit and integration tests for data extraction mechanisms."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.extractors.scraper import WebExtractor


@pytest.mark.asyncio
async def test_web_extractor_fetch_and_parse_success():
    """Validates that WebExtractor extracts DOM elements, headings, and metadata."""
    mock_html = (
        "<html><head><title>Market Tech Corp</title>"
        "<meta name='description' content='Leading cloud data solutions'></head>"
        "<body><h1>Enterprise AI</h1><p>We build resilient distributed systems for data intelligence.</p></body></html>"
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    mock_response.url = "https://example.com/company"
    mock_response.headers = {"content-type": "text/html"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        extractor = WebExtractor()
        result = await extractor.extract("https://example.com/company")

        assert result["status_code"] == 200
        assert result["title"] == "Market Tech Corp"
        assert result["meta_description"] == "Leading cloud data solutions"
        assert len(result["headings"]) == 1
        assert result["headings"][0]["text"] == "Enterprise AI"
        assert result["word_count"] > 0
        assert result["is_fallback"] is False


@pytest.mark.asyncio
async def test_web_extractor_fallback_on_network_failure():
    """Validates that WebExtractor triggers structured fallback upon request exception."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Connection refused")

        extractor = WebExtractor()
        result = await extractor.extract("https://unreachable-endpoint.com")

        assert result["is_fallback"] is True
        assert "Connection refused" in result.get("error", "")
