"""Global state schema definitions for the LangGraph market intelligence pipeline.

Maintains typed graph state channels, execution metadata, extracted content,
and error aggregation via Annotated reducers.
"""

import operator
from typing import Annotated, Any, Dict, List
from typing_extensions import TypedDict


class PipelineState(TypedDict):
    """Global state schema traversing all nodes in the intelligence pipeline.

    Attributes:
        target_url: The target market intelligence URL to inspect and scrape.
        raw_data: Extracted raw data payload including HTML, headers, status and metadata.
        cleaned_data: Sanitized, normalized, and validated data structure.
        analysis: Structured competitive intelligence report and analytical insights.
        confidence_score: Quantitative reliability metric for the extraction and analysis (0.0 to 1.0).
        retry_count: Number of execution cycles performed when confidence is below threshold.
        errors: Cumulative list of errors encountered across node executions, reduced via list concatenation.
    """

    target_url: str
    raw_data: Dict[str, Any]
    cleaned_data: Dict[str, Any]
    analysis: Dict[str, Any]
    confidence_score: float
    retry_count: int
    errors: Annotated[List[str], operator.add]
