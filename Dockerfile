# Use an argument for the Python version to allow flexibility in choosing the base image.
ARG PYTHON_VERSION=3.13-slim

# Use a multi-stage build to optimize the final image size by separating the build environment from the runtime environment.

# Stage 1: Build stage - Install dependencies and create a virtual environment.
FROM python:${PYTHON_VERSION} AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV UV_NO_CACHE=1

# Install system build and runtime dependencies needed to compile Python packages.
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libgdal-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY README.md ./

# Create the virtual environment from the locked dependency set.
RUN uv sync --frozen --no-dev

# Stage 2: Final stage - Use a smaller base image and copy only the necessary runtime files.
FROM base AS final

ENV PATH="/app/.venv/bin:$PATH"
ENV DJANGO_SETTINGS_MODULE=core.settings
ENV PYTHONPATH="/app"

# Install only runtime system packages for the final image.
RUN apt-get update && apt-get install -y \
    libpq5 \
    libgdal36 \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create a non-root user for safer container execution.
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --from=base /app/.venv /app/.venv

# Ensure the non-root user can read and execute the virtual environment.
RUN chown -R appuser:appuser /app/.venv \
    && chmod -R 755 /app/.venv

USER appuser

EXPOSE 8000
