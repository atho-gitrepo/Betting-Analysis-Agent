FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install specific versions to avoid NumPy 2.x
COPY requirements.txt .
RUN pip install --no-cache-dir numpy==1.24.3
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download T5 model
RUN python -c "from transformers import T5Tokenizer, T5ForConditionalGeneration; T5Tokenizer.from_pretrained('t5-small'); T5ForConditionalGeneration.from_pretrained('t5-small')" || true

COPY . .

CMD ["python", "analytics_service.py"]
