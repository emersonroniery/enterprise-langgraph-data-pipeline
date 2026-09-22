"""Functional tests for the LangGraph market intelligence workflow."""

import pytest
from unittest.mock import AsyncMock, patch
from src.graph.workflow import create_pipeline_graph, evaluate_confidence_and_retry
from src.graph.state import PipelineState
from langgraph.graph import END


@pytest.mark.asyncio
async def test_pipeline_graph_successful_flow():
    """Verifies that high-confidence extraction flows directly to END."""
    app = create_pipeline_graph()

    mock_raw_data = {
        "url": "https://company.com",
        "status_code": 200,
        "title": "Enterprise Cloud Analytics",
        "meta_description": "Data pipelines and intelligence platform",
        "headings": [
            {"level": "H1", "text": "Platform Overview"},
            {"level": "H2", "text": "Enterprise Features"},
            {"level": "H3", "text": "Developer API & Pricing"},
        ],
        "paragraphs": ["Deep text content " * 30],
        "raw_text": "Deep text content " * 30,
        "word_count": 180,
        "is_fallback": False,
    }

    with patch("src.extractors.scraper.WebExtractor.extract", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = mock_raw_data

        initial_state: PipelineState = {
            "target_url": "https://company.com",
            "raw_data": {},
            "cleaned_data": {},
            "analysis": {},
            "confidence_score": 0.0,
            "retry_count": 0,
            "errors": [],
        }

        final_state = await app.ainvoke(initial_state)

        assert final_state["confidence_score"] >= 0.70
        assert final_state["retry_count"] == 0
        assert "Enterprise Cloud Analytics" in final_state["cleaned_data"]["title"]
        assert "executive_summary" in final_state["analysis"]


@pytest.mark.asyncio
async def test_conditional_router_retry_and_termination():
    """Verifies conditional routing decisions based on confidence and retries."""
    # Low confidence with retry budget -> route to 'extract'
    low_confidence_state: PipelineState = {
        "target_url": "https://empty-page.com",
        "raw_data": {},
        "cleaned_data": {},
        "analysis": {},
        "confidence_score": 0.45,
        "retry_count": 0,
        "errors": [],
    }
    assert evaluate_confidence_and_retry(low_confidence_state) == "extract"

    # Low confidence with exhausted retries -> route to END
    exhausted_state: PipelineState = {
        "target_url": "https://empty-page.com",
        "raw_data": {},
        "cleaned_data": {},
        "analysis": {},
        "confidence_score": 0.45,
        "retry_count": 2,
        "errors": [],
    }
    assert evaluate_confidence_and_retry(exhausted_state) == END

    # High confidence -> route to END
    high_confidence_state: PipelineState = {
        "target_url": "https://valid-page.com",
        "raw_data": {},
        "cleaned_data": {},
        "analysis": {},
        "confidence_score": 0.85,
        "retry_count": 0,
        "errors": [],
    }
    assert evaluate_confidence_and_retry(high_confidence_state) == END
