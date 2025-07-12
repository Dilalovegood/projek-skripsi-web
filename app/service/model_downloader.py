import os
import requests
from urllib.parse import urlparse

def download_model():
    """Download model dari URL yang disediakan"""
    model_url = os.environ.get('MODEL_URL', 'https://your-model-url.com/vit_model.pth')
    model_path = 'models/vit_model.pth'
    
    if not os.path.exists(model_path):
        try:
            print("📥 Downloading model...")
            os.makedirs('models', exist_ok=True)
            
            response = requests.get(model_url, stream=True)
            response.raise_for_status()
            
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("✅ Model downloaded successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to download model: {e}")
            return False
    
    return True

def download_model_from_gcs():
    """Download model dari Google Cloud Storage"""
    bucket_name = os.environ.get('GCS_BUCKET')
    model_path = 'models/vit_model.pth'
    
    if not os.path.exists(model_path) and bucket_name:
        try:
            print("📥 Downloading model from GCS...")
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob('models/vit_model.pth')
            
            os.makedirs('models', exist_ok=True)
            blob.download_to_filename(model_path)
            
            print("✅ Model downloaded from GCS")
            return True
        except Exception as e:
            print(f"❌ Failed to download model from GCS: {e}")
            return False
    
    return os.path.exists(model_path)
