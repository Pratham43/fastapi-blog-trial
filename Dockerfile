# Use official lightweight Python image
FROM python:3.13-slim AS builder

# Install uv for extremely fast, reliable dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtualenv
RUN uv sync --frozen --no-dev

# Final runtime stage
FROM python:3.13-slim

# Install system utilities if needed (like libpq for postgres, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtualenv and application code
COPY --from=builder /app/.venv /app/.venv
COPY . /app

# Ensure we use the virtualenv python
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8060

# Default command to run migrations and start the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8060"]
