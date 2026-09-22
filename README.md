# Enterprise LangGraph Data Pipeline

[![CI](https://github.com/emersonroniery/enterprise-langgraph-data-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/emersonroniery/enterprise-langgraph-data-pipeline/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/orchestration-LangGraph%20%3E%3D%200.2.0-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Pydantic v2](https://img.shields.io/badge/validation-Pydantic%20v2-green.svg)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, asynchronous market intelligence and data extraction pipeline orchestrated with **LangGraph**, **Pydantic v2**, **HTTPX**, and **PostgreSQL**. The pipeline features automated retry loops driven by quantitative confidence scoring, structured DOM extraction, and enterprise-grade observability.

---

## 🏛️ System Architecture

```mermaid
graph TD
    classDef startEnd fill:#2563eb,stroke:#1d4ed8,stroke-width:2px,color:#fff;
    classDef nodeClass fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef decision fill:#d97706,stroke:#b45309,stroke-width:2px,color:#fff;

    START([START]) :::startEnd --> extract[extract_node<br/><i>Async Web Extraction with Fallback</i>] :::nodeClass
    extract --> sanitize[sanitize_node<br/><i>Pydantic v2 Normalization & Schema Validation</i>] :::nodeClass
    sanitize --> analyst[analyst_node<br/><i>Market Intelligence Synthesis & Confidence Scoring</i>] :::nodeClass
    
    analyst --> evaluate{evaluate_confidence_and_retry<br/><i>confidence < 0.70 AND retries < 2?</i>} :::decision
    
    evaluate -- Yes (Retry Loop) --> extract
    evaluate -- No (Threshold Met or Retries Exhausted) --> END([END]) :::startEnd
```

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Workflow Orchestration** | [LangGraph](https://github.com/langchain-ai/langgraph) (>=0.2.0) | Directed state graph with conditional feedback routing |
| **Data Validation** | [Pydantic v2](https://docs.pydantic.dev/) & `pydantic-settings` | Strict runtime schema enforcement and environment config |
| **Web Extraction** | [HTTPX](https://www.python-httpx.org/) & [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) | High-concurrency async fetching with resilient DOM parsing |
| **Relational Storage** | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) & [PostgreSQL](https://www.postgresql.org/) | Audit runs and extracted document persistence |
| **Observability** | [Loguru](https://github.com/Delgan/loguru) | Structured stdout logging with rotating file sinks |
| **Quality & Testing** | [Pytest](https://docs.pytest.org/), `pytest-asyncio`, [Ruff](https://docs.astral.sh/ruff/) | Asynchronous test suites and ultra-fast static analysis |
| **Infrastructure** | [Docker](https://www.docker.com/) & Docker Compose | Hardened multi-stage containerization with non-root security |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.11+
- Docker & Docker Compose (optional for containerized execution)
- Git

### 2. Local Environment Setup

```bash
# Clone the repository
git clone https://github.com/emersonroniery/enterprise-langgraph-data-pipeline.git
cd enterprise-langgraph-data-pipeline

# Copy environment variables template
cp .env.example .env

# Create and activate virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install pinned dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Running the Pipeline

Execute the compiled state graph with the built-in market intelligence demonstration:

```bash
python -m src.graph.workflow
```

Sample output:
```text
2026-09-22 20:53:05 | INFO | Starting Enterprise LangGraph Market Intelligence Pipeline
2026-09-22 20:53:05 | INFO | Executing extract_node on https://news.ycombinator.com (attempt 0)
2026-09-22 20:53:06 | INFO | Executing sanitize_node for https://news.ycombinator.com
2026-09-22 20:53:06 | INFO | Executing analyst_node for https://news.ycombinator.com
2026-09-22 20:53:06 | INFO | Pipeline Execution Completed Successfully
2026-09-22 20:53:07 | INFO | Final Confidence Score : 0.85
```

---

## 🐳 Docker & Docker Compose Orchestration

The project includes an optimized, non-root `Dockerfile` and a multi-container `docker-compose.yml` service orchestration stack:

```bash
# Navigate to docker directory and start all services
cd docker
docker compose up --build
```

### Services Included:
1. **`postgres`**: PostgreSQL 16 Alpine instance with continuous healthcheck probing (`pg_isready`) and volume persistence (`postgres_data`).
2. **`pipeline`**: Production Python 3.11 runtime executing under an unprivileged `appuser` (UID 1001), synchronized with the healthy database service.

To shut down services and remove networks:
```bash
docker compose down -v
```

---

## 🧪 Testing & Code Quality

Run the comprehensive test suite with mocks:

```bash
# Execute unit and graph flow tests
pytest -v

# Run Ruff linter
ruff check .

# Verify code formatting
ruff format --check .
```

---

## 📁 Repository Structure

```plaintext
enterprise-langgraph-data-pipeline/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI pipeline (Ruff + Pytest + Postgres)
├── docker/
│   ├── Dockerfile               # Production hardened Python 3.11-slim container
│   └── docker-compose.yml       # Multi-service stack (App + PostgreSQL with healthcheck)
├── docs/
│   └── architecture.md          # Architectural blueprints and component specifications
├── logs/                        # Runtime rotated logs sink
├── src/
│   ├── __init__.py
│   ├── config.py                # BaseSettings management with Pydantic v2
│   ├── extractors/
│   │   ├── __init__.py
│   │   └── scraper.py           # Async WebExtractor with structured fallback
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── nodes.py             # Pure functional nodes (extract, sanitize, analyst)
│   │   ├── state.py             # PipelineState TypedDict with Annotated reducers
│   │   └── workflow.py          # StateGraph assembly with conditional retry router
│   ├── storage/
│   │   ├── __init__.py
│   │   └── database.py          # SQLAlchemy 2.0 ORM models and session management
│   └── utils/
│       ├── __init__.py
│       └── logger.py            # Loguru configuration with structured formatting
├── tests/
│   ├── __init__.py
│   ├── test_extractors.py       # Unit tests for web extraction and fallbacks
│   └── test_graph_flow.py       # End-to-end tests for StateGraph and retry edge
├── .dockerignore                # Docker build context exclusions
├── .env.example                 # Environment template with mock credentials
├── .gitignore                   # Git ignore definitions
├── LICENSE                      # MIT License
├── pyproject.toml               # Build system, Ruff, and Pytest configuration
└── requirements.txt             # Pinned production dependencies
```

---

## 📄 License

This project is licensed under the terms of the [MIT License](LICENSE).
