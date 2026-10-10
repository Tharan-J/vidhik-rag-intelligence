FROM python:3.11-slim

# Suppress banner noise and ensure immediate log output
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TF_ENABLE_ONEDNN_OPTS=0 \
    PORT=8008

WORKDIR /app

# Install minimal build and curl dependencies for health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY prototype/requirements.txt /app/prototype/requirements.txt
RUN pip install --no-cache-dir -r /app/prototype/requirements.txt

# Copy backend code, index data, and supporting metadata
COPY prototype/ /app/prototype/
COPY research/rag_readiness_audit/master_document_audit.csv /app/research/rag_readiness_audit/master_document_audit.csv
COPY frontend/src/lib/data/extracted_matters.json /app/frontend/src/lib/data/extracted_matters.json

# Expose listening port
EXPOSE 8008

# Health probe probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8008}/health || exit 1

# Run Vidhik retrieval daemon on Railway's dynamic PORT
CMD ["sh", "-c", "python /app/prototype/scripts/retrieval_daemon.py ${PORT:-8008}"]
