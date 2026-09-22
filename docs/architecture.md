# Enterprise LangGraph Data Pipeline

## Overview
High-throughput, resilient enterprise data extraction and processing pipeline powered by LangGraph, Playwright, and PostgreSQL.

## Architecture
- **Extractors (`src/extractors`)**: Asynchronous data retrieval via Playwright and HTTPX.
- **Graph Engine (`src/graph`)**: Directed state graph orchestrating extraction, validation, enrichment, and storage.
- **Storage Layer (`src/storage`)**: SQLAlchemy ORM persistence layer connected to PostgreSQL.
- **Observability (`src/utils`)**: Structured logging with Loguru.
