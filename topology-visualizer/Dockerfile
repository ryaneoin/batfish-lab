FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy parsers
COPY parsers/ /app/parsers/

# Copy pipeline script
COPY run_pipeline.py .

# Create output directory
RUN mkdir -p /app/output

# Set Python path
ENV PYTHONPATH=/app

CMD ["python", "run_pipeline.py"]
