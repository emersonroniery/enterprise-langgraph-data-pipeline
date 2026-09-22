"""LangGraph orchestration workflow and state graph compilation.

Assembles extraction, sanitization, analytical synthesis, and confidence-driven
conditional retry loops for market intelligence pipelines.
"""

import asyncio
import json
from typing import Literal

from langgraph.graph import END, START, StateGraph

from src.config import settings
from src.graph.nodes import analyst_node, extract_node, sanitize_node
from src.graph.state import PipelineState
from src.utils.logger import logger


def evaluate_confidence_and_retry(
    state: PipelineState,
) -> Literal["extract", "__end__"]:
    """Conditional router: checks confidence score against threshold and retry limits.

    If confidence_score < 0.7 and retry_count < 2, loops back to 'extract'.
    Otherwise, terminates execution at END.

    Args:
        state: The current pipeline state containing confidence_score and retry_count.

    Returns:
        Next node name: 'extract' for retry loop, or '__end__' to finalize.
    """
    confidence = state.get("confidence_score", 0.0)
    retries = state.get("retry_count", 0)

    logger.info(
        "Evaluating router conditions -> Confidence: {:.2f} (threshold: {}), Retries: {} (max: {})",
        confidence,
        settings.MIN_CONFIDENCE_THRESHOLD,
        retries,
        settings.MAX_RETRIES,
    )

    if confidence < settings.MIN_CONFIDENCE_THRESHOLD and retries < settings.MAX_RETRIES:
        logger.warning(
            "Confidence {:.2f} below target threshold {}. Triggering re-extraction attempt {}...",
            confidence,
            settings.MIN_CONFIDENCE_THRESHOLD,
            retries + 1,
        )
        return "extract"

    logger.info("Confidence criteria satisfied or max retries reached. Finalizing pipeline.")
    return END


def create_pipeline_graph():
    """Builds and compiles the StateGraph workflow with conditional feedback loop.

    Workflow topology:
        START -> extract -> sanitize -> analyst --(confidence >= 0.7 or retries >= 2)--> END
                                            |
                                            +--(confidence < 0.7 and retries < 2)-----> extract

    Returns:
        Compiled StateGraph runnable.
    """
    workflow = StateGraph(PipelineState)

    # Register graph nodes
    workflow.add_node("extract", extract_node)
    workflow.add_node("sanitize", sanitize_node)
    workflow.add_node("analyst", analyst_node)

    # Establish linear edges
    workflow.add_edge(START, "extract")
    workflow.add_edge("extract", "sanitize")
    workflow.add_edge("sanitize", "analyst")

    # Establish conditional feedback edge
    workflow.add_conditional_edges(
        "analyst",
        evaluate_confidence_and_retry,
        {
            "extract": "extract",
            END: END,
        },
    )

    return workflow.compile()


async def main() -> None:
    """Demonstrates an end-to-end practical execution of the intelligence pipeline."""
    sample_target_url = "https://news.ycombinator.com"

    logger.info("==================================================================")
    logger.info("Starting Enterprise LangGraph Market Intelligence Pipeline")
    logger.info("Target URL: {}", sample_target_url)
    logger.info("==================================================================")

    initial_state: PipelineState = {
        "target_url": sample_target_url,
        "raw_data": {},
        "cleaned_data": {},
        "analysis": {},
        "confidence_score": 0.0,
        "retry_count": 0,
        "errors": [],
    }

    pipeline = create_pipeline_graph()

    # Execute workflow asynchronously
    final_state = await pipeline.ainvoke(initial_state)

    logger.info("==================================================================")
    logger.info("Pipeline Execution Completed Successfully")
    logger.info("Final Confidence Score : {:.2f}", final_state["confidence_score"])
    logger.info("Total Retries Performed: {}", final_state["retry_count"])
    logger.info("Report Summary         : {}", final_state["analysis"].get("executive_summary"))
    logger.info("Market Signals         : {}", final_state["analysis"].get("market_signals"))
    if final_state["errors"]:
        logger.warning("Pipeline Error Logs    : {}", final_state["errors"])
    logger.info("==================================================================")

    # Pretty print structured JSON output for CLI demonstration
    print("\n--- [STRUCTURED INTELLIGENCE OUTPUT] ---")
    print(json.dumps(final_state["analysis"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
