# ============================================================
# TalentUP Fichaje — Backend Dockerfile
# ============================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies required by psycopg2 / bcrypt / reportlab
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ ./app/

# Expose the port the app runs on
EXPOSE 8000

# Run with uvicorn — $PORT is set at runtime (default 8000)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
