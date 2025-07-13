import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import timm
import numpy as np
import base64
import io
import os

class SkinTypePredictor:
    def __init__(self, model_path, device=None):
        self.device = device if device else torch.device('cpu')
        self.model_path = model_path
        self.model = None
        self.class_names = ['berminyak', 'kering', 'kombinasi', 'normal']
        
        # Load model
        self.load_model()
        
        # Define transforms
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def load_model(self):
        """Load the vit_model.pth"""
        try:
            print(f"Loading model from: {self.model_path}")
            
            # Load checkpoint
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            # Create ViT model
            self.model = timm.create_model('vit_base_patch16_224', 
                                         pretrained=False, 
                                         num_classes=len(self.class_names))
            
            # Load state dict (ignore mismatches)
            self.model.load_state_dict(checkpoint, strict=False)
            
            # Set to evaluation mode
            self.model.eval()
            self.model.to(self.device)
            
            print("✅ Model loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise e
    
    def preprocess_image(self, image):
        """Preprocess image for prediction"""
        try:
            # Handle different input types
            if isinstance(image, str):
                # Base64 string
                if image.startswith('data:image'):
                    image = image.split(',')[1]
                image_data = base64.b64decode(image)
                image = Image.open(io.BytesIO(image_data))
            elif isinstance(image, np.ndarray):
                # Numpy array
                image = Image.fromarray(image)
            elif hasattr(image, 'read'):
                # File-like object
                image = Image.open(image)
            
            # Convert to RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Apply transforms
            image_tensor = self.transform(image).unsqueeze(0)
            return image_tensor.to(self.device)
            
        except Exception as e:
            print(f"Error in preprocessing: {e}")
            raise e
    
    def predict(self, image):
        """Make prediction on image"""
        try:
            # Preprocess image
            input_tensor = self.preprocess_image(image)
            
            # Make prediction
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                confidence, predicted = torch.max(probabilities, 1)
                
                # Get all probabilities
                all_probs = probabilities.cpu().numpy()[0]
                
                return {
                    'predicted_class': self.class_names[predicted.item()],
                    'confidence': float(confidence.item()),
                    'probabilities': {
                        self.class_names[i]: float(prob) 
                        for i, prob in enumerate(all_probs)
                    }
                }
                
        except Exception as e:
            print(f"Error in prediction: {e}")
            return {
                'error': str(e),
                'predicted_class': 'normal',
                'confidence': 0.5,
                'probabilities': {name: 0.25 for name in self.class_names}
            }

# Global predictor instance
predictor = None

def initialize_model(model_path=None):
    """Initialize the global predictor"""
    global predictor
    try:
        if model_path is None:
            from app.config import Config
            model_path = Config.MODEL_PATH
        
        print(f"Initializing model from: {model_path}")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        predictor = SkinTypePredictor(model_path, device=torch.device('cpu'))
        print("✅ Model initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize model: {e}")
        return False

def get_prediction(image):
    """Get prediction from global predictor"""
    try:
        if predictor is None:
            return {'error': 'Model not initialized'}
        
        return predictor.predict(image)
        
    except Exception as e:
        print(f"Error in get_prediction: {e}")
        return {
            'error': f'Prediction failed: {str(e)}',
            'predicted_class': 'normal',
            'confidence': 0.5,
            'probabilities': {'berminyak': 0.25, 'kering': 0.25, 'kombinasi': 0.25, 'normal': 0.25}
        }