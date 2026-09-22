# ==============================================================================
# Enterprise LangGraph Data Pipeline - Production Dockerfile
# Optimized Multi-layer build based on python:3.11-slim with non-root security
# ==============================================================================

FROM python:3.11-slim AS base

# Python runtime and build optimization flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install minimal OS dependencies required for PostgreSQL and network connectivity
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user and group for enterprise compliance
RUN groupadd -r -g 1001 appgroup && \
    useradd -r -u 1001 -g appgroup -d /app -s /bin/false appuser

# Leverage Docker layer caching by installing dependencies before copying source code
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application source code and configuration
COPY . .

# Ensure appuser ownership of application files and runtime logs directory
RUN mkdir -p /app/logs && \
    chown -R appuser:appgroup /app

# Switch to unprivileged execution user
USER appuser

# Default pipeline entrypoint
CMD ["python", "-m", "src.graph.workflow"]
