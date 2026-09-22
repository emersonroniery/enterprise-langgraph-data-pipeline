"""Functional tests for the LangGraph workflow execution pipeline."""

import pytest
from src.graph.workflow import create_pipeline_graph
from src.graph.state import PipelineState


@pytest.mark.asyncio
async def test_pipeline_graph_compilation_and_execution():
    """Verifies that the compiled LangGraph workflow executes end-to-end through all nodes."""
    app = create_pipeline_graph()

    initial_state: PipelineState = {
        "pipeline_id": "test-pipeline-run-001",
        "target_urls": ["https://example.com/item1", "https://example.com/item2"],
        "raw_documents": [],
        "processed_records": [],
        "errors": [],
        "metadata": {"environment": "test"},
        "is_completed": False,
    }

    final_state = await app.ainvoke(initial_state)

    assert final_state["is_completed"] is True
    assert len(final_state["raw_documents"]) == 2
    assert len(final_state["processed_records"]) == 2
    assert final_state["metadata"].get("persisted_records") == 2
    assert len(final_state["errors"]) == 0


@pytest.mark.asyncio
async def test_pipeline_graph_error_branching():
    """Verifies that errors route execution directly to error_handler_node."""
    app = create_pipeline_graph()

    faulty_state: PipelineState = {
        "pipeline_id": "test-faulty-run-002",
        "target_urls": [],
        "raw_documents": [],
        "processed_records": [],
        "errors": ["Extraction failed due to network timeout"],
        "metadata": {"environment": "test"},
        "is_completed": False,
    }

    final_state = await app.ainvoke(faulty_state)

    assert final_state["is_completed"] is False
    assert final_state["metadata"].get("failed") is True
