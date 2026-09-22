"""LangGraph functional nodes executing market intelligence processing.

Includes:
1. extract_node: Network fetching via WebExtractor with resilience.
2. sanitize_node: Strict data normalization and validation via Pydantic schemas.
3. analyst_node: Analytical synthesis, competitive summary generation, and confidence scoring.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl
from src.config import settings
from src.extractors.scraper import WebExtractor
from src.graph.state import PipelineState
from src.utils.logger import logger


# =====================================================================
# Pydantic Validation Schemas
# =====================================================================

class HeadingModel(BaseModel):
    """Normalized heading item."""
    level: str
    text: str


class SanitizedMarketData(BaseModel):
    """Pydantic schema enforcing clean and validated market extraction payloads."""

    url: str = Field(description="Normalized target URL")
    title: str = Field(default="", description="Sanitized web page title")
    meta_description: str = Field(default="", description="Cleaned meta description")
    headings: List[HeadingModel] = Field(default_factory=list, description="Extracted structural headings")
    cleaned_text: str = Field(default="", description="Sanitized readable body text")
    word_count: int = Field(default=0, ge=0, description="Total word count in body text")
    is_fallback: bool = Field(default=False, description="Whether fallback extraction was utilized")
    http_status: int = Field(default=200, description="HTTP response status code")
    sanitized_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of sanitization",
    )

    @property
    def has_sufficient_content(self) -> bool:
        """Determines if the extracted content meets minimum analytical density."""
        return self.word_count >= 50 and bool(self.title or self.headings)


class IntelligenceAnalysis(BaseModel):
    """Structured competitive intelligence report and confidence evaluation."""

    executive_summary: str = Field(description="High-level synthesis of value proposition and offerings")
    key_themes: List[str] = Field(default_factory=list, description="Extracted commercial or technical themes")
    market_signals: List[str] = Field(default_factory=list, description="Identified competitive advantages or signals")
    content_quality: str = Field(description="Evaluation of source content quality (HIGH, MEDIUM, LOW)")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Quantitative reliability score (0.0 to 1.0)")
    analyzed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of intelligence generation",
    )


# =====================================================================
# Pure LangGraph Nodes
# =====================================================================

async def extract_node(state: PipelineState) -> Dict[str, Any]:
    """Node: Consumes target_url, invokes WebExtractor, and populates raw_data.

    Args:
        state: The current pipeline state containing target_url and retry_count.

    Returns:
        State dictionary updates with raw_data, incremented retry_count on retry, and errors.
    """
    url = state["target_url"]
    current_retry = state.get("retry_count", 0)

    # Increment retry counter if re-entering extraction from analyst node
    if "confidence_score" in state and state["confidence_score"] is not None:
        current_retry += 1

    logger.info("Executing extract_node on {} (attempt {})", url, current_retry)

    extractor = WebExtractor()
    errors: List[str] = []

    try:
        raw_result = await extractor.extract(url, attempt=current_retry)
        if raw_result.get("status_code", 500) >= 400:
            errors.append(f"HTTP error {raw_result.get('status_code')} during extraction of {url}")
    except Exception as exc:
        logger.error("Unexpected failure in extract_node: {}", exc)
        raw_result = {
            "url": url,
            "status_code": 500,
            "error": str(exc),
            "title": "",
            "meta_description": "",
            "headings": [],
            "paragraphs": [],
            "raw_text": "",
            "word_count": 0,
        }
        errors.append(f"Extraction exception: {exc}")

    return {
        "raw_data": raw_result,
        "retry_count": current_retry,
        "errors": errors,
    }


async def sanitize_node(state: PipelineState) -> Dict[str, Any]:
    """Node: Normalizes raw_data into a strict Pydantic SanitizedMarketData schema.

    Args:
        state: Pipeline state containing raw_data.

    Returns:
        State dictionary updates with cleaned_data.
    """
    logger.info("Executing sanitize_node for {}", state["target_url"])
    raw = state.get("raw_data", {})
    errors: List[str] = []

    try:
        headings_raw = raw.get("headings", [])
        headings_models = [
            HeadingModel(level=h.get("level", "H2"), text=h.get("text", "").strip())
            for h in headings_raw
            if h.get("text")
        ]

        cleaned_model = SanitizedMarketData(
            url=str(raw.get("url", state["target_url"])),
            title=str(raw.get("title", "")).strip(),
            meta_description=str(raw.get("meta_description", "")).strip(),
            headings=headings_models,
            cleaned_text=str(raw.get("raw_text", "")).strip(),
            word_count=int(raw.get("word_count", 0)),
            is_fallback=bool(raw.get("is_fallback", False)),
            http_status=int(raw.get("status_code", 200)),
        )

        cleaned_dict = cleaned_model.model_dump(mode="json")
    except Exception as exc:
        logger.error("Data sanitization failed: {}", exc)
        errors.append(f"Sanitization error: {exc}")
        cleaned_dict = {
            "url": state["target_url"],
            "title": "",
            "meta_description": "",
            "headings": [],
            "cleaned_text": "",
            "word_count": 0,
            "is_fallback": True,
            "http_status": 500,
            "sanitized_at": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "cleaned_data": cleaned_dict,
        "errors": errors,
    }


async def analyst_node(state: PipelineState) -> Dict[str, Any]:
    """Node: Synthesizes competitive intelligence and computes confidence score.

    Args:
        state: Pipeline state containing cleaned_data and target_url.

    Returns:
        State dictionary updates with analysis and confidence_score.
    """
    logger.info("Executing analyst_node for {}", state["target_url"])
    cleaned = state.get("cleaned_data", {})
    text = cleaned.get("cleaned_text", "")
    title = cleaned.get("title", "")
    word_count = cleaned.get("word_count", 0)
    headings = cleaned.get("headings", [])
    http_status = cleaned.get("http_status", 200)

    # 1. Compute quantitative confidence score (0.0 to 1.0)
    confidence = 0.0

    if http_status == 200:
        confidence += 0.30
    elif http_status < 400:
        confidence += 0.15

    if title:
        confidence += 0.20

    if len(headings) >= 3:
        confidence += 0.20
    elif len(headings) >= 1:
        confidence += 0.10

    if word_count >= 150:
        confidence += 0.30
    elif word_count >= 50:
        confidence += 0.15
    elif word_count > 0:
        confidence += 0.05

    confidence = round(min(max(confidence, 0.0), 1.0), 2)

    # 2. Synthesize Competitive Intelligence Insights
    quality_label = "HIGH" if confidence >= 0.8 else ("MEDIUM" if confidence >= 0.6 else "LOW")

    key_themes = [h.get("text") for h in headings[:5]] if headings else ["General Web Presence"]
    
    executive_summary = (
        f"Competitive intelligence profile for '{title or state['target_url']}'. "
        f"Extracted {word_count} words across {len(headings)} sections. "
        f"Identified primary offerings focusing on: {', '.join(key_themes[:3])}."
    )

    signals = []
    if "pricing" in text.lower() or "plans" in text.lower():
        signals.append("Public pricing model identified")
    if "enterprise" in text.lower() or "b2b" in text.lower():
        signals.append("Enterprise / B2B market positioning")
    if "api" in text.lower() or "developer" in text.lower():
        signals.append("Developer ecosystem / API-first capabilities")
    if not signals:
        signals.append("Standard digital footprint / introductory tier")

    analysis_report = IntelligenceAnalysis(
        executive_summary=executive_summary,
        key_themes=key_themes,
        market_signals=signals,
        content_quality=quality_label,
        confidence_score=confidence,
    )

    logger.info(
        "Analysis complete for {}. Confidence: {} | Quality: {}",
        state["target_url"],
        confidence,
        quality_label,
    )

    return {
        "analysis": analysis_report.model_dump(mode="json"),
        "confidence_score": confidence,
    }
