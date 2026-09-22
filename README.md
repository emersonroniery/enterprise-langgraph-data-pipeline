# Enterprise LangGraph Data Pipeline

Production-ready asynchronous data extraction, transformation, enrichment, and persistence pipeline orchestrated with **LangGraph**, **Playwright**, and **PostgreSQL**.

---

## Architecture Directory Structure

```plaintext
enterprise-langgraph-data-pipeline/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI workflow (linting, tests, db services)
├── docker/
│   ├── Dockerfile               # Production multi-stage Docker build
│   └── docker-compose.yml       # Local stack with PostgreSQL service
├── docs/
│   └── architecture.md          # Architectural blueprints and component details
├── src/
│   ├── __init__.py
│   ├── config.py                # Pydantic BaseSettings management
│   ├── extractors/
│   │   ├── __init__.py
│   │   └── scraper.py           # Playwright & HTTPX scraper engine
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── nodes.py             # LangGraph functional nodes
│   │   ├── state.py             # TypedDict pipeline state schema
│   │   └── workflow.py          # StateGraph assembly & compilation
│   ├── storage/
│   │   ├── __init__.py
│   │   └── database.py          # SQLAlchemy 2.0 ORM models and session factory
│   └── utils/
│       ├── __init__.py
│       └── logger.py            # Loguru structured logging configuration
├── tests/
│   ├── __init__.py
│   ├── test_extractors.py       # Unit tests for scrapers
│   └── test_graph_flow.py       # End-to-end graph workflow tests
├── .env.example                 # Template for required environment variables
├── .gitignore                   # Git ignore patterns
├── pyproject.toml               # Build configuration, Ruff and Pytest settings
└── requirements.txt             # Pinned core dependencies
```

---

## Quickstart

### 1. Environment Setup
```bash
# Copy environment configuration
cp .env.example .env

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 2. Run Tests & Linter
```bash
# Run Ruff linting
ruff check .

# Run asynchronous test suite
pytest -v
```

### 3. Run with Docker Compose
```bash
cd docker
docker-compose up --build
```
