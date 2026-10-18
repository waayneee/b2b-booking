FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies with pre-built wheels only
RUN pip install --no-cache-dir --only-binary :all: --upgrade pip setuptools && \
    pip install --no-cache-dir --only-binary :all: -r requirements.txt || \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 8000

# Start command
CMD ["sh", "-c", "cd /app && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
