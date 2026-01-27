# =============================================================================
# Multi-stage Dockerfile for Essivi Django Backend
# Optimized for production with security best practices
# =============================================================================

# --- Build Stage ---
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn uvicorn[standard]

# --- Runtime Stage ---
FROM python:3.11-slim

# Labels for container metadata
LABEL maintainer="Essivi Team" \
    version="1.0" \
    description="Essivi Django Backend with ASGI support"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=core.settings \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Copy project source into container
COPY . /app

# Create entrypoint script for Render (WSGI with Gunicorn)
RUN printf '#!/bin/bash\n\
    set -e\n\
    echo "=========================================="\n\
    echo "  Essivi Backend - Starting on Render..."\n\
    echo "=========================================="\n\
    echo "[1/2] Applying database migrations..."\n\
    python manage.py migrate --noinput\n\
    echo "[2/2] Collecting static files..."\n\
    python manage.py collectstatic --noinput\n\
    echo "=========================================="\n\
    echo "  Starting Gunicorn WSGI Server..."\n\
    echo "=========================================="\n\
    exec gunicorn --bind 0.0.0.0:$PORT app:app --workers 2 --threads 2\n\
    ' > /entrypoint.sh && chmod +x /entrypoint.sh

# Create non-root user for security
RUN addgroup --system --gid 1000 essivi && \
    adduser --system --uid 1000 --gid 1000 --no-create-home essivi && \
    chown -R essivi:essivi /app && \
    mkdir -p /app/staticfiles /app/media && \
    chown -R essivi:essivi /app/staticfiles /app/media

USER essivi

EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/schema/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]
