# Use an official Python runtime as a parent image
FROM python:3.14-slim-bookworm AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# --frozen ensures we stick to the lockfile
RUN uv sync --frozen --no-dev --no-install-project

# Final stage
FROM python:3.14-slim-bookworm

WORKDIR /app

# Install runtime dependencies (e.g. libpq for psycopg)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed environment from builder
COPY --from=builder /app/.venv /app/.venv

# Update PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy project files
COPY . .
RUN chmod +x /app/entrypoint.sh

# Collect static files (can be overridden or handled in entrypoint)
# RUN python manage.py collectstatic --noinput

# Expose port (gunicorn default)
EXPOSE 8000

# Default command (can be overridden by compose)
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
