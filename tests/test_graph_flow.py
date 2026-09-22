"""Functional and unit test suite for LangGraph market intelligence workflow.

Covers:
- StateGraph compilation and topology verification
- Direct conditional edge routing logic
- High-confidence scenario (> 0.70) terminating directly at END
- Low-confidence scenario (< 0.70) triggering retry loop through extract_node
"""

from unittest.mock import AsyncMock, patch

import pytest
from langgraph.graph import END

from src.graph.state import PipelineState
from src.graph.workflow import create_pipeline_graph, evaluate_confidence_and_retry


def test_state_graph_compilation():
    """Validates that the StateGraph compiles properly with all registered nodes and edges."""
    app = create_pipeline_graph()
    assert app is not None
    # Verify presence of expected node identifiers in graph definition
    node_keys = list(app.get_graph().nodes.keys())
    assert "extract" in node_keys
    assert "sanitize" in node_keys
    assert "analyst" in node_keys


@pytest.mark.asyncio
async def test_pipeline_graph_high_confidence_flow():
    """Scenario: High-confidence extraction (>= 0.7) processes cleanly and terminates at END without retry."""
    app = create_pipeline_graph()

    mock_rich_data = {
        "url": "https://enterprise-saas.com",
        "status_code": 200,
        "title": "Enterprise Cloud Data Intelligence",
        "meta_description": "Real-time market analytics and competitive data pipeline",
        "headings": [
            {"level": "H1", "text": "Platform Architecture"},
            {"level": "H2", "text": "Core Capabilities"},
            {"level": "H3", "text": "Pricing & API Documentation"},
        ],
        "paragraphs": ["Comprehensive analytics platform for enterprise data teams." * 20],
        "raw_text": "Comprehensive analytics platform for enterprise data teams. " * 20,
        "word_count": 180,
        "is_fallback": False,
    }

    with patch(
        "src.extractors.scraper.WebExtractor.extract", new_callable=AsyncMock
    ) as mock_extract:
        mock_extract.return_value = mock_rich_data

        initial_state: PipelineState = {
            "target_url": "https://enterprise-saas.com",
            "raw_data": {},
            "cleaned_data": {},
            "analysis": {},
            "confidence_score": 0.0,
            "retry_count": 0,
            "errors": [],
        }

        final_state = await app.ainvoke(initial_state)

        # Assertions
        assert final_state["confidence_score"] >= 0.70
        assert final_state["retry_count"] == 0
        assert mock_extract.await_count == 1
        assert "Enterprise Cloud Data Intelligence" in final_state["cleaned_data"]["title"]
        assert "executive_summary" in final_state["analysis"]
        assert final_state["analysis"]["content_quality"] in ["HIGH", "MEDIUM"]


@pytest.mark.asyncio
async def test_pipeline_graph_low_confidence_triggers_retry_loop():
    """Scenario: Low-confidence extraction (< 0.7) triggers conditional retry back to extract_node."""
    app = create_pipeline_graph()

    # Initial extraction returns sparse content (low confidence ~0.5), triggering retry
    sparse_data = {
        "url": "https://sparse-landing.com",
        "status_code": 200,
        "title": "Under Construction",
        "meta_description": "",
        "headings": [],
        "paragraphs": ["Coming soon."],
        "raw_text": "Coming soon.",
        "word_count": 2,
        "is_fallback": False,
    }

    with patch(
        "src.extractors.scraper.WebExtractor.extract", new_callable=AsyncMock
    ) as mock_extract:
        mock_extract.return_value = sparse_data

        initial_state: PipelineState = {
            "target_url": "https://sparse-landing.com",
            "raw_data": {},
            "cleaned_data": {},
            "analysis": {},
            "confidence_score": 0.0,
            "retry_count": 0,
            "errors": [],
        }

        final_state = await app.ainvoke(initial_state)

        # Extraction must have run initial attempt + 2 retries (total 3 extractions, max retries reached)
        assert mock_extract.await_count == 3
        assert final_state["confidence_score"] < 0.70
        assert final_state["retry_count"] == 2
        assert final_state["analysis"]["content_quality"] == "LOW"


def test_conditional_router_decisions():
    """Unit test for evaluate_confidence_and_retry edge function."""
    # 1. Low confidence with remaining retry budget -> 'extract'
    state_retry: PipelineState = {
        "target_url": "https://example.com",
        "raw_data": {},
        "cleaned_data": {},
        "analysis": {},
        "confidence_score": 0.50,
        "retry_count": 0,
        "errors": [],
    }
    assert evaluate_confidence_and_retry(state_retry) == "extract"

    # 2. Low confidence with exhausted retry budget -> END
    state_exhausted: PipelineState = {
        "target_url": "https://example.com",
        "raw_data": {},
        "cleaned_data": {},
        "analysis": {},
        "confidence_score": 0.50,
        "retry_count": 2,
        "errors": [],
    }
    assert evaluate_confidence_and_retry(state_exhausted) == END

    # 3. High confidence -> END immediately
    state_success: PipelineState = {
        "target_url": "https://example.com",
        "raw_data": {},
        "cleaned_data": {},
        "analysis": {},
        "confidence_score": 0.85,
        "retry_count": 0,
        "errors": [],
    }
    assert evaluate_confidence_and_retry(state_success) == END
