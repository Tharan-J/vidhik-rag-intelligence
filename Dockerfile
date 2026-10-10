FROM python:3.11-slim

# Suppress banner noise and ensure immediate log output
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TF_ENABLE_ONEDNN_OPTS=0 \
    PORT=8008

WORKDIR /app

# Install minimal curl dependency for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Pre-install CPU-only PyTorch from official PyTorch CPU wheel repository.
# This prevents pip from downloading ~4GB of NVIDIA CUDA/cuDNN/NCCL packages.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install minimal production runtime dependencies
COPY prototype/requirements-prod.txt /app/prototype/requirements-prod.txt
RUN pip install --no-cache-dir -r /app/prototype/requirements-prod.txt

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
