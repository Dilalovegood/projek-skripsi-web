#!/usr/bin/env python3

import requests
import base64
import io
from PIL import Image

def test_predict_endpoint():
    """Test the /predict endpoint"""
    
    # Create a test image
    test_image = Image.new('RGB', (224, 224), color=(128, 128, 128))
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    test_image.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    # Test 1: File upload
    print("🔄 Testing file upload...")
    try:
        files = {'image': ('test.jpg', img_bytes, 'image/jpeg')}
        response = requests.post('http://localhost:8080/predict', files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ File upload test passed!")
        else:
            print("❌ File upload test failed!")
            
    except Exception as e:
        print(f"❌ File upload test error: {e}")
    
    # Test 2: Base64 upload
    print("\n🔄 Testing base64 upload...")
    try:
        img_bytes.seek(0)
        img_b64 = base64.b64encode(img_bytes.read()).decode('utf-8')
        
        json_data = {'image_data': f'data:image/jpeg;base64,{img_b64}'}
        response = requests.post('http://localhost:8080/predict', json=json_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Base64 upload test passed!")
        else:
            print("❌ Base64 upload test failed!")
            
    except Exception as e:
        print(f"❌ Base64 upload test error: {e}")
    
    # Test 3: Health check
    print("\n🔄 Testing health endpoint...")
    try:
        response = requests.get('http://localhost:8080/health')
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Health check test passed!")
        else:
            print("❌ Health check test failed!")
            
    except Exception as e:
        print(f"❌ Health check test error: {e}")

if __name__ == "__main__":
    test_predict_endpoint()
