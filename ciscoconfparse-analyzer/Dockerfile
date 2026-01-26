FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy analysis scripts
COPY analyzer/ /app/analyzer/

# Set the configs directory as a volume mount point
VOLUME ["/configs"]

# Default command runs the analysis
CMD ["python", "-u", "analyzer/main.py"]
