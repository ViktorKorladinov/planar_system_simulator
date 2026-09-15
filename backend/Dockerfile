# ==========================================
# Stage 1: Build & Dependencies
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install compilation headers and libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest first for layer caching
COPY requirements.txt .

# Install dependencies into isolated installation prefix
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ==========================================
# Stage 2: Production Runtime
# ==========================================
FROM python:3.11-slim AS runner

# Install lightweight runtime dependencies (PostgreSQL client library and curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Security: Create non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application source code
COPY --chown=appuser:appgroup api ./api
COPY --chown=appuser:appgroup clients ./clients
COPY --chown=appuser:appgroup core ./core
COPY --chown=appuser:appgroup db ./db
COPY --chown=appuser:appgroup domain ./domain
COPY --chown=appuser:appgroup mappers ./mappers
COPY --chown=appuser:appgroup services ./services
COPY --chown=appuser:appgroup solvers ./solvers
COPY --chown=appuser:appgroup templates* ./templates/
COPY --chown=appuser:appgroup alembic ./alembic
COPY --chown=appuser:appgroup alembic.ini .
COPY --chown=appuser:appgroup dependencies.py .
COPY --chown=appuser:appgroup main.py .
COPY --chown=appuser:appgroup entrypoint.sh .

# Ensure data plot and templates directories exist and are writable by non-root user
RUN mkdir -p /app/data/plots /app/templates && \
    chown -R appuser:appgroup /app/data /app/templates && \
    chmod +x /app/entrypoint.sh

USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
