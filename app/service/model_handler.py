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
        """Load the vit_model.pth specifically"""
        try:
            print(f"🔄 Loading vit_model.pth from: {self.model_path}")
            
            # Check file exists and get size
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"vit_model.pth not found at: {self.model_path}")
            
            file_size = os.path.getsize(self.model_path) / (1024 * 1024)  # MB
            print(f"📊 Model file size: {file_size:.2f} MB")
            
            # Load checkpoint
            print("🔄 Loading checkpoint...")
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            # Debug checkpoint structure
            if isinstance(checkpoint, dict):
                print(f"📋 Checkpoint keys: {list(checkpoint.keys())}")
                state_dict = checkpoint
            else:
                state_dict = checkpoint
            
            # Check if it's the expected ViT structure
            sample_keys = list(state_dict.keys())[:5]
            print(f"🔍 Sample keys: {sample_keys}")
            
            # Look for head structure to determine classes
            head_keys = [k for k in state_dict.keys() if 'head' in k.lower()]
            print(f"🎯 Head keys found: {head_keys}")
            
            # Create the model based on your vit_model.pth structure
            print("🏗️ Creating ViT model...")
            
            # Based on your logs, it seems to be a standard ViT with custom head
            if any('heads.head.1.weight' in k for k in state_dict.keys()):
                print("🔧 Detected custom head structure (heads.head.1)")
                
                # Create base ViT model
                self.model = timm.create_model('vit_base_patch16_224', 
                                             pretrained=False, 
                                             num_classes=len(self.class_names))
                
                # Modify head to match the checkpoint structure
                # Your model seems to have heads.head.1 structure
                self.model.head = nn.Sequential(
                    nn.Dropout(0.1),
                    nn.Linear(768, len(self.class_names))  # ViT-B has 768 features
                )
                
                # Load state dict with custom mapping
                model_state = {}
                for key, value in state_dict.items():
                    if key.startswith('heads.head.1'):
                        # Map heads.head.1.weight -> head.1.weight
                        new_key = key.replace('heads.head.1', 'head.1')
                        model_state[new_key] = value
                    else:
                        model_state[key] = value
                
                # Load with strict=False to handle any mismatches
                missing_keys, unexpected_keys = self.model.load_state_dict(model_state, strict=False)
                
                if missing_keys:
                    print(f"⚠️ Missing keys: {len(missing_keys)}")
                if unexpected_keys:
                    print(f"⚠️ Unexpected keys: {len(unexpected_keys)}")
                
            else:
                # Standard ViT loading
                print("🔧 Using standard ViT loading")
                self.model = timm.create_model('vit_base_patch16_224', 
                                             pretrained=False, 
                                             num_classes=len(self.class_names))
                
                # Try to load state dict
                missing_keys, unexpected_keys = self.model.load_state_dict(state_dict, strict=False)
                
                if missing_keys:
                    print(f"⚠️ Missing keys: {len(missing_keys)}")
                    # Reinitialize head if needed
                    if any('head' in key for key in missing_keys):
                        print("🔄 Reinitializing head layer...")
                        self.model.head = nn.Linear(768, len(self.class_names))
        
            # Set model to evaluation mode
            self.model.eval()
            self.model.to(self.device)
            
            print(f"✅ vit_model.pth loaded successfully on {self.device}")
            
            # Test model with dummy input
            print("🧪 Testing model with dummy input...")
            dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
            with torch.no_grad():
                test_output = self.model(dummy_input)
                print(f"✅ Model test successful - output shape: {test_output.shape}")
        
        except Exception as e:
            print(f"❌ Error loading vit_model.pth: {e}")
            import traceback
            traceback.print_exc()
            
            # Don't create fallback model in production
            raise Exception(f"Failed to load vit_model.pth: {e}")
    
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
            print(f"🔄 Starting prediction with image type: {type(image)}")
            
            # Validate model is loaded
            if self.model is None:
                raise Exception("Model not loaded")
            
            # Preprocess image
            print("🔄 Preprocessing image...")
            input_tensor = self.preprocess_image(image)
            print(f"✅ Image preprocessed, tensor shape: {input_tensor.shape}")
            
            # Make prediction
            print("🔄 Running model inference...")
            with torch.no_grad():
                outputs = self.model(input_tensor)
                print(f"✅ Model outputs shape: {outputs.shape}")
                
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                confidence, predicted = torch.max(probabilities, 1)
                
                # Get all probabilities
                all_probs = probabilities.cpu().numpy()[0]
                
                result = {
                    'predicted_class': self.class_names[predicted.item()],
                    'confidence': float(confidence.item()),
                    'probabilities': {
                        self.class_names[i]: float(prob) 
                        for i, prob in enumerate(all_probs)
                    }
                }
                
                print(f"✅ Prediction complete: {result['predicted_class']} ({result['confidence']:.3f})")
                return result
                
        except Exception as e:
            print(f"❌ Error in prediction: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'predicted_class': 'normal',  # fallback
                'confidence': 0.5,
                'probabilities': {name: 0.25 for name in self.class_names}
            }

# Global predictor instance
predictor = None

def is_model_loaded():
    """Check if model is loaded and ready"""
    global predictor
    return predictor is not None and predictor.model is not None

def initialize_model(model_path=None):
    """Initialize the global predictor with vit_model.pth"""
    global predictor
    try:
        # Use default path if none provided
        if model_path is None:
            from app.config import Config
            model_path = Config.MODEL_PATH
        
        print(f"🔄 Initializing vit_model.pth from: {model_path}")
        
        # Validate the specific model file
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"vit_model.pth not found at: {model_path}")
        
        if not model_path.endswith('vit_model.pth'):
            print(f"⚠️ Warning: Expected vit_model.pth but got: {os.path.basename(model_path)}")
            
        # Force CPU for Cloud Run stability
        device = torch.device('cpu')
        print(f"🖥️ Using device: {device}")
        
        predictor = SkinTypePredictor(model_path, device=device)
        print(f"✅ vit_model.pth initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize vit_model.pth: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_prediction(image):
    """Get prediction from global predictor"""
    try:
        if predictor is None:
            print("❌ Model not initialized")
            return {'error': 'Model not initialized'}
        
        if predictor.model is None:
            print("❌ Model object is None")
            return {'error': 'Model object not loaded'}
        
        print(f"🔄 Making prediction with image type: {type(image)}")
        result = predictor.predict(image)
        print(f"✅ Prediction completed: {result.get('predicted_class', 'error')}")
        return result
        
    except Exception as e:
        print(f"❌ Error in get_prediction: {e}")
        import traceback
        traceback.print_exc()
        return {
            'error': f'Prediction failed: {str(e)}',
            'predicted_class': 'normal',  # fallback
            'confidence': 0.5,
            'probabilities': {'berminyak': 0.25, 'kering': 0.25, 'kombinasi': 0.25, 'normal': 0.25}
        }

def find_model_file(model_dir):
    """Find model file in directory (supports both .pt and .pth)"""
    model_extensions = ['.pt', '.pth']
    
    for ext in model_extensions:
        for file in os.listdir(model_dir):
            if file.endswith(ext):
                return os.path.join(model_dir, file)
    
    return None