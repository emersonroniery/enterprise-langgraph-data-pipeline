"""LangGraph workflow definition and state graph compiler.

Assembles nodes, standard edges, conditional routing, and error branches
into a production-grade compiled graph instance.
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from src.graph.state import PipelineState
from src.graph.nodes import (
    extract_node,
    transform_node,
    enrich_node,
    load_node,
    error_handler_node,
)


def should_continue(state: PipelineState) -> Literal["continue", "error"]:
    """Conditional router: Determines whether to proceed with transformation or fault handling."""
    if state.get("errors") and len(state["errors"]) > 0:
        return "error"
    return "continue"


def create_pipeline_graph():
    """Builds and compiles the production LangGraph data pipeline.

    Returns:
        Compiled StateGraph instance ready for invocation and streaming.
    """
    workflow = StateGraph(PipelineState)

    # Register Nodes
    workflow.add_node("extract", extract_node)
    workflow.add_node("transform", transform_node)
    workflow.add_node("enrich", enrich_node)
    workflow.add_node("load", load_node)
    workflow.add_node("error_handler", error_handler_node)

    # Establish Workflow Edges
    workflow.add_edge(START, "extract")

    workflow.add_conditional_edges(
        "extract",
        should_continue,
        {
            "continue": "transform",
            "error": "error_handler",
        },
    )

    workflow.add_edge("transform", "enrich")
    workflow.add_edge("enrich", "load")
    workflow.add_edge("load", END)
    workflow.add_edge("error_handler", END)

    # Compile the graph
    app = workflow.compile()
    return app
