FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Verify vit_model.pth exists
RUN ls -la models/ && \
    if [ ! -f "models/vit_model.pth" ]; then \
        echo "❌ vit_model.pth not found in models/ directory"; \
        exit 1; \
    else \
        echo "✅ vit_model.pth found"; \
        ls -lh models/vit_model.pth; \
    fi

# Create uploads directory
RUN mkdir -p app/static/uploads

# Expose port
EXPOSE 8080

# Run with specific settings for vit_model.pth
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "300", "--preload", "app:app"]
