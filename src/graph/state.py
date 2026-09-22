"""Pipeline state schema definitions for LangGraph.

Maintains typed graph state, intermediate artifacts, execution metadata, and error tracing.
"""

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
import operator


class PipelineState(TypedDict):
    """Represents the global state passed between nodes in the LangGraph data pipeline.

    Attributes:
        pipeline_id: Unique identifier for the pipeline run.
        target_urls: List of URLs scheduled for extraction.
        raw_documents: Raw extracted documents / HTML / text payloads.
        processed_records: Structured and validated entity records ready for storage.
        errors: Aggregated list of operational errors encountered across nodes.
        metadata: Execution context, metrics, and runtime flags.
        is_completed: Flag indicating terminal state reached.
    """

    pipeline_id: str
    target_urls: List[str]
    raw_documents: Annotated[List[Dict[str, Any]], operator.add]
    processed_records: Annotated[List[Dict[str, Any]], operator.add]
    errors: Annotated[List[str], operator.add]
    metadata: Dict[str, Any]
    is_completed: bool
