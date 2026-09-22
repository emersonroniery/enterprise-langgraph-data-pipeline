"""LangGraph orchestration graph package.

Defines state schemas, node computations, and compiled state graph workflows.
"""

from typing import TYPE_CHECKING

from src.graph.state import PipelineState

if TYPE_CHECKING:
    from src.graph.workflow import create_pipeline_graph

__all__ = ["PipelineState", "create_pipeline_graph"]


def __getattr__(name: str):
    if name == "create_pipeline_graph":
        from src.graph.workflow import create_pipeline_graph

        return create_pipeline_graph
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
