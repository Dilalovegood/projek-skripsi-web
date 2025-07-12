#!/bin/bash

# Deploy script untuk Google Cloud Run
# Pastikan gcloud CLI sudah terinstall dan dikonfigurasi

set -e

# Configuration
PROJECT_ID="your-project-id"  # Ganti dengan Project ID Anda
REGION="us-central1"
SERVICE_NAME="scan-skin"

echo "🚀 Starting deployment to Google Cloud Run..."

# 1. Set project
echo "📋 Setting project to $PROJECT_ID"
gcloud config set project $PROJECT_ID

# 2. Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 3. Check if model file exists
if [ ! -f "models/vit_model.pth" ]; then
    echo "❌ Error: Model file not found at models/vit_model.pth"
    echo "Please ensure your trained model is available before deploying."
    exit 1
fi

echo "✅ Model file found: $(ls -lh models/vit_model.pth)"

# 4. Submit build to Cloud Build
echo "🏗️ Building and deploying with Cloud Build..."
gcloud builds submit --config cloudbuild.yaml .

# 5. Get service URL
echo "🔍 Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo "✅ Deployment successful!"
echo "🌐 Service URL: $SERVICE_URL"
echo "🏥 Health check: $SERVICE_URL/health"
echo "🔮 Prediction endpoint: $SERVICE_URL/predict"
echo ""
echo "📊 To test your deployment:"
echo "curl -X GET $SERVICE_URL/health"
echo ""
echo "🎯 To view logs:"
echo "gcloud logs tail --service=$SERVICE_NAME"
