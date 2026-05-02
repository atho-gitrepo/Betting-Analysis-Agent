FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir numpy==1.24.3
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download T5 model
RUN python -c "from transformers import T5Tokenizer, T5ForConditionalGeneration; T5Tokenizer.from_pretrained('t5-small'); T5ForConditionalGeneration.from_pretrained('t5-small')" || true

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data cache

# Make scripts executable
RUN chmod +x railway_start.sh process_manager.py

# Health check uses PORT env var
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl --fail http://localhost:${PORT:-8080}/_stcore/health || exit 1

# Use railway start script
CMD ["./railway_start.sh"]