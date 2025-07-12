import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    DEBUG = os.environ.get('FLASK_ENV') != 'production'
    
    # Model configuration - direct path to vit_model.pth
    MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models')
    MODEL_PATH = os.path.join(MODEL_DIR, 'vit_model.pth')
    
    # Validate model exists
    if not os.path.exists(MODEL_PATH):
        print(f"⚠️ Model file not found at: {MODEL_PATH}")
        print(f"📁 Looking in directory: {MODEL_DIR}")
        if os.path.exists(MODEL_DIR):
            files = os.listdir(MODEL_DIR)
            print(f"📄 Files found: {files}")
        else:
            print(f"❌ Model directory doesn't exist: {MODEL_DIR}")
    else:
        print(f"✅ Model found at: {MODEL_PATH}")
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # Allowed extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}