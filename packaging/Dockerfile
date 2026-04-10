FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy source
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir \
    flask \
    cryptography \
    requests

# Expose API port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/api/health || exit 1

# Start REST API
CMD ["python3", "-m", "agentsoul.adapters.rest_api"]
