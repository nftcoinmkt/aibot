FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy uv configuration files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy application code
COPY . .

# Create directories for tenant databases and uploads
RUN mkdir -p ./tenant_databases ./uploads

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app

# Run the application
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
