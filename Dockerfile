# Use a lightweight Python image
FROM python:3.11-slim

# Create working directory
WORKDIR /app

# Install system dependencies (for building pip packages like cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (helps Docker cache layers)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Expose Render default port (Render sets $PORT automatically)
EXPOSE 10000

# Start server (Render will replace $PORT with real port)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
