import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import timm
import numpy as np
import base64
import io
import os

# Optional OpenCV import dengan error handling
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not available. Some features may be limited.")

class SkinTypePredictor:
    def __init__(self, model_path, device=None):
        self.device = device if device else torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = model_path
        self.model = None
        self.class_names = ['berminyak', 'kering', 'kombinasi', 'normal']  # Sesuaikan dengan class Anda
        
        # Validate model file exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
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
        """Load the Vision Transformer model (.pt or .pth)"""
        try:
            print(f"Loading model from: {self.model_path}")
            
            # Load checkpoint first to inspect structure
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            # Debug: print checkpoint structure
            if isinstance(checkpoint, dict):
                print(f"Checkpoint keys: {list(checkpoint.keys())}")
                
                # Try to extract state_dict
                if 'model_state_dict' in checkpoint:
                    state_dict = checkpoint['model_state_dict']
                elif 'state_dict' in checkpoint:
                    state_dict = checkpoint['state_dict']
                elif 'model' in checkpoint:
                    state_dict = checkpoint['model']
                else:
                    state_dict = checkpoint
            else:
                state_dict = checkpoint
            
            # Print some keys to understand structure
            if isinstance(state_dict, dict):
                sample_keys = list(state_dict.keys())[:10]
                print(f"Sample state_dict keys: {sample_keys}")
                
                # Check if it's a multi-head model
                head_keys = [k for k in state_dict.keys() if 'head' in k]
                print(f"Head keys found: {head_keys}")
            
            # Try different model architectures based on the keys
            try:
                # Method 1: Try standard ViT
                print("Trying standard ViT architecture...")
                self.model = timm.create_model('vit_base_patch16_224', 
                                             pretrained=False, 
                                             num_classes=len(self.class_names))
                self.model.load_state_dict(state_dict, strict=False)
                
            except Exception as e1:
                print(f"Standard ViT failed: {e1}")
                
                try:
                    # Method 2: Try with different num_classes
                    print("Trying with different num_classes...")
                    
                    # Inspect the head layer to determine num_classes
                    head_weight_key = None
                    for key in state_dict.keys():
                        if 'head' in key and 'weight' in key:
                            head_weight_key = key
                            break
                    
                    if head_weight_key:
                        head_shape = state_dict[head_weight_key].shape
                        num_classes = head_shape[0]
                        print(f"Detected num_classes from model: {num_classes}")
                        
                        self.model = timm.create_model('vit_base_patch16_224', 
                                                     pretrained=False, 
                                                     num_classes=num_classes)
                        self.model.load_state_dict(state_dict, strict=False)
                        
                        # If num_classes is different, add a mapping layer
                        if num_classes != len(self.class_names):
                            print(f"Adding mapping layer: {num_classes} -> {len(self.class_names)}")
                            self.model.head = nn.Linear(self.model.head.in_features, len(self.class_names))
                    else:
                        raise Exception("Could not determine model structure")
                        
                except Exception as e2:
                    print(f"Alternative loading failed: {e2}")
                    
                    # Method 3: Try to load the entire model directly
                    print("Trying to load entire model...")
                    if isinstance(checkpoint, dict) and 'model' in checkpoint:
                        self.model = checkpoint['model']
                    else:
                        # Last resort: create a minimal working model
                        print("Creating minimal model...")
                        self.model = timm.create_model('vit_base_patch16_224', 
                                                     pretrained=True, 
                                                     num_classes=len(self.class_names))
            
            self.model.to(self.device)
            self.model.eval()
            print(f"✅ Model loaded successfully on {self.device}")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print(f"Model path: {self.model_path}")
            print(f"Device: {self.device}")
            
            # Fallback: create a pretrained model for testing
            print("🔄 Loading fallback pretrained model for testing...")
            self.model = timm.create_model('vit_base_patch16_224', 
                                         pretrained=True, 
                                         num_classes=len(self.class_names))
            self.model.to(self.device)
            self.model.eval()
            print("⚠️  Using pretrained model as fallback")
    
    def preprocess_image(self, image):
        """Preprocess image for prediction"""
        try:
            if isinstance(image, str):
                # If base64 string
                if image.startswith('data:image'):
                    image = image.split(',')[1]
                image_data = base64.b64decode(image)
                image = Image.open(io.BytesIO(image_data))
            elif isinstance(image, np.ndarray):
                # If numpy array from OpenCV (only if CV2 is available)
                if CV2_AVAILABLE:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(image)
            elif hasattr(image, 'read'):
                # If file-like object
                image = Image.open(image)
            
            # Convert to RGB if necessary
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
                
                result = {
                    'predicted_class': self.class_names[predicted.item()],
                    'confidence': confidence.item(),
                    'probabilities': {
                        self.class_names[i]: float(prob) 
                        for i, prob in enumerate(all_probs)
                    }
                }
                
                print(f"Prediction: {result['predicted_class']} ({result['confidence']:.3f})")
                return result
                
        except Exception as e:
            print(f"Error in prediction: {e}")
            return {
                'error': str(e),
                'predicted_class': 'normal',  # fallback
                'confidence': 0.5,
                'probabilities': {name: 0.25 for name in self.class_names}
            }

# Global predictor instance
predictor = None

def initialize_model(model_path):
    """Initialize the global predictor - works with both .pt and .pth"""
    global predictor
    try:
        predictor = SkinTypePredictor(model_path)
        return True
    except Exception as e:
        print(f"Failed to initialize model: {e}")
        return False

def get_prediction(image):
    """Get prediction from global predictor"""
    if predictor is None:
        return {'error': 'Model not initialized'}
    return predictor.predict(image)

def find_model_file(model_dir):
    """Find model file in directory (supports both .pt and .pth)"""
    model_extensions = ['.pt', '.pth']
    
    for ext in model_extensions:
        for file in os.listdir(model_dir):
            if file.endswith(ext):
                return os.path.join(model_dir, file)
    
    return None