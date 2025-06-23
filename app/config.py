import os

def get_model_path():
    """Find model file in models directory"""
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models')
    
    # Look for specific filenames first
    preferred_names = [
        'vit_model.pth',
        'skin_type_model.pt',
        'skin_type_model.pth',
        'model.pt', 
        'model.pth',
        'best_model.pt',
        'best_model.pth'
    ]
    
    for name in preferred_names:
        path = os.path.join(model_dir, name)
        if os.path.exists(path):
            return path
    
    # If no preferred names found, look for any .pt or .pth file
    if os.path.exists(model_dir):
        for file in os.listdir(model_dir):
            if file.endswith(('.pt', '.pth')):
                return os.path.join(model_dir, file)
    
    return None

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    DEBUG = True
    
    # Model configuration - auto-detect .pt or .pth
    MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models')
    MODEL_PATH = get_model_path()
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # Allowed extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}