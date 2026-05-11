FROM python:3.12-slim

WORKDIR /app

# Install curl (used by Compose health-check) + coreutils for tee
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        coreutils \
    && rm -rf /var/lib/apt/lists/*

# Log directory for Promtail file-based ingestion
RUN mkdir -p /var/log/app

# Dependency install layer (cacheable)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY main.py instrumentation.py inference.py ./

EXPOSE 8000

# tee stdout to a shared-volume log file so Promtail can tail it cross-platform
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port 8000 --log-level warning 2>&1 | tee /var/log/app/app.log"
