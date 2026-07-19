# ============================================================
# TalentUP Fichaje — Production-ready Backend Dockerfile
# ============================================================
# Multi-stage build using python:3.11-slim, non-root user and
# a built-in health check. The resulting image runs Uvicorn with
# graceful shutdown support.
# ============================================================

# ---------- Build stage ----------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System dependencies required to compile/ install packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY backend/requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# ---------- Runtime stage ----------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Make sure the embedded venv binaries are found
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app

# Runtime system libraries needed by psycopg2 / bcrypt / reportlab
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user/group
RUN groupadd --gid 1000 talentup && \
    useradd --uid 1000 --gid talentup --home-dir "$APP_HOME" --shell /bin/false talentup

WORKDIR $APP_HOME

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY --chown=talentup:talentup backend/app ./app

# Persist SQLite fallback only for dev/tests (empty directory, owned by app user)
RUN mkdir -p "$APP_HOME/data" && chown -R talentup:talentup "$APP_HOME"

USER talentup

EXPOSE 8000

# Health check against the public health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${PORT:-8000}/api/health || exit 1

# Run with uvicorn. $PORT can be overridden at runtime (Railway, etc.).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
