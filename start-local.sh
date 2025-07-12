#!/bin/bash

# Script untuk testing aplikasi secara lokal

echo "🚀 Starting ScanSkin App with Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if model file exists
if [ ! -f "models/vit_model.pth" ]; then
    echo "⚠️  Model file not found at models/vit_model.pth"
    echo "📁 Please ensure your model file is in the models/ directory"
    
    # List files in models directory
    if [ -d "models" ]; then
        echo "📋 Files in models/ directory:"
        ls -la models/
    else
        echo "❌ models/ directory not found"
        exit 1
    fi
fi

# Build and run with docker-compose
echo "🔨 Building Docker image..."
docker-compose build

echo "🏃 Starting application..."
docker-compose up -d

echo "✅ Application is starting..."
echo "🌐 Open your browser and go to: http://localhost:5001"
echo "📋 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"

# Wait a bit and check if container is running
sleep 5
if docker-compose ps | grep -q "Up"; then
    echo "✅ Container is running successfully!"
else
    echo "❌ Container failed to start. Check logs:"
    docker-compose logs
fi
