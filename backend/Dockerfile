# ScholarForge Backend Dockerfile
# Multi-stage build for production

# ================= Stage 1: Builder =================
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install -e ".[dev]" || \
    (pip install fastapi uvicorn[standard] pydantic pydantic-settings sqlalchemy asyncpg aiosqlite alembic redis elasticsearch neo4j python-jose[cryptography] PyJWT passlib[bcrypt] python-multipart httpx aiohttp celery openai anthropic tiktoken langchain langchain-community sentence-transformers websockets y-py pytest pytest-asyncio)

# ================= Stage 2: Production =================
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app

# Create app directory
WORKDIR $APP_HOME

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . $APP_HOME/

# Create non-root user
RUN groupadd -r scholarforge && useradd -r -g scholarforge scholarforge \
    && chown -R scholarforge:scholarforge $APP_HOME

# Switch to non-root user
USER scholarforge

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
