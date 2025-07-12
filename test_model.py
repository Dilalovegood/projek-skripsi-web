#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.service.model_handler import initialize_model, get_prediction, is_model_loaded
from PIL import Image
import io
import base64

def test_model_loading():
    """Test model loading and prediction"""
    print("=== Testing Model Loading ===")
    
    model_path = "/Volumes/SamsungT7/python/projek-skripsi-scanSkin/models/vit_model.pth"
    
    print(f"1. Model file exists: {os.path.exists(model_path)}")
    print(f"2. Model file size: {os.path.getsize(model_path) / (1024*1024):.2f} MB")
    
    # Test model initialization
    print("\n=== Initializing Model ===")
    success = initialize_model(model_path)
    print(f"3. Model initialization success: {success}")
    print(f"4. Model loaded check: {is_model_loaded()}")
    
    if not success:
        print("❌ Model initialization failed!")
        return False
    
    # Test with a dummy image
    print("\n=== Testing Prediction ===")
    try:
        # Create a test image
        test_image = Image.new('RGB', (224, 224), color=(128, 128, 128))
        print("5. Created test image")
        
        # Test prediction
        result = get_prediction(test_image)
        print(f"6. Prediction result: {result}")
        
        if 'error' in result:
            print(f"❌ Prediction failed: {result['error']}")
            return False
        else:
            print(f"✅ Prediction successful: {result['predicted_class']} ({result['confidence']:.3f})")
            return True
            
    except Exception as e:
        print(f"❌ Exception during prediction test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_model_loading()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")
    sys.exit(0 if success else 1)
