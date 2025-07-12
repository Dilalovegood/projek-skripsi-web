#!/usr/bin/env python3

import requests
import base64
import io
import json
from PIL import Image, ImageDraw
import os

def create_test_image():
    """Create a realistic test image for skin analysis"""
    # Create a skin-like test image
    image = Image.new('RGB', (400, 400), color=(220, 180, 140))  # Skin tone
    
    # Add some texture and patterns
    draw = ImageDraw.Draw(image)
    
    # Add some spots to simulate skin texture
    for i in range(20):
        x = i * 20
        y = i * 15
        draw.ellipse([x, y, x+5, y+5], fill=(200, 160, 120))
    
    # Add a larger feature
    draw.ellipse([150, 150, 250, 250], fill=(240, 200, 160))
    
    return image

def test_upload_methods():
    """Test all upload methods comprehensively"""
    
    BASE_URL = "http://localhost:8080"  # Change for local testing
    # BASE_URL = "https://scan-skin-1065584510816.us-central1.run.app"  # For cloud testing
    
    print("🧪 Starting comprehensive upload tests...")
    
    # Create test image
    test_image = create_test_image()
    print(f"✅ Created test image: {test_image.size}")
    
    # Test 1: JSON with base64
    print("\n" + "="*50)
    print("🧪 Test 1: JSON with base64...")
    try:
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='JPEG', quality=90)
        img_bytes.seek(0)
        
        img_b64 = base64.b64encode(img_bytes.read()).decode('utf-8')
        
        json_data = {'image_data': f'data:image/jpeg;base64,{img_b64}'}
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(f'{BASE_URL}/predict', 
                               json=json_data, 
                               headers=headers,
                               timeout=30)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ JSON test passed!")
            print(f"   Prediction: {result.get('predicted_class', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0):.3f}")
            print(f"   Image saved: {result.get('image_filename', 'None')}")
            print(f"   Image source: {result.get('image_source', 'unknown')}")
        else:
            print(f"❌ JSON test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ JSON test error: {e}")
    
    # Test 2: File upload
    print("\n" + "="*50)
    print("🧪 Test 2: File upload...")
    try:
        # Save test image to temp file
        temp_file = io.BytesIO()
        test_image.save(temp_file, format='JPEG', quality=90)
        temp_file.seek(0)
        
        files = {'image': ('test_skin.jpg', temp_file, 'image/jpeg')}
        
        response = requests.post(f'{BASE_URL}/predict', 
                               files=files,
                               timeout=30)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ File upload test passed!")
            print(f"   Prediction: {result.get('predicted_class', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0):.3f}")
            print(f"   Image saved: {result.get('image_filename', 'None')}")
            print(f"   Image source: {result.get('image_source', 'unknown')}")
        else:
            print(f"❌ File upload test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ File upload test error: {e}")
    
    # Test 3: Form data with base64
    print("\n" + "="*50)
    print("🧪 Test 3: Form data with base64...")
    try:
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='JPEG', quality=90)
        img_bytes.seek(0)
        
        img_b64 = base64.b64encode(img_bytes.read()).decode('utf-8')
        
        data = {'image_data': f'data:image/jpeg;base64,{img_b64}'}
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(f'{BASE_URL}/predict', 
                               data=data, 
                               headers=headers,
                               timeout=30)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Form data test passed!")
            print(f"   Prediction: {result.get('predicted_class', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0):.3f}")
            print(f"   Image saved: {result.get('image_filename', 'None')}")
            print(f"   Image source: {result.get('image_source', 'unknown')}")
        else:
            print(f"❌ Form data test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Form data test error: {e}")
    
    # Test 4: Health check
    print("\n" + "="*50)
    print("🧪 Test 4: Health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Health check passed!")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Health check failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_image_formats():
    """Test different image formats"""
    
    BASE_URL = "http://localhost:8080"
    
    print("\n" + "="*60)
    print("🧪 Testing different image formats...")
    
    test_image = create_test_image()
    
    formats = [
        ('JPEG', 'image/jpeg', '.jpg'),
        ('PNG', 'image/png', '.png'),
        ('WEBP', 'image/webp', '.webp')
    ]
    
    for format_name, mime_type, ext in formats:
        print(f"\n🔍 Testing {format_name} format...")
        try:
            img_bytes = io.BytesIO()
            
            # Handle different formats
            if format_name == 'WEBP':
                try:
                    test_image.save(img_bytes, format=format_name, quality=90)
                except Exception:
                    print(f"⚠️ {format_name} not supported, skipping...")
                    continue
            else:
                test_image.save(img_bytes, format=format_name, quality=90)
            
            img_bytes.seek(0)
            
            files = {
                'image': (f'test_skin{ext}', img_bytes, mime_type)
            }
            
            response = requests.post(f'{BASE_URL}/predict', 
                                   files=files,
                                   timeout=30)
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {format_name} test passed!")
                print(f"   Prediction: {result.get('predicted_class', 'unknown')}")
                print(f"   Image saved: {result.get('image_filename', 'None')}")
            else:
                print(f"❌ {format_name} test failed: {response.text}")
                
        except Exception as e:
            print(f"❌ {format_name} test error: {e}")

def test_error_cases():
    """Test error handling"""
    
    BASE_URL = "http://localhost:8080"
    
    print("\n" + "="*60)
    print("🧪 Testing error cases...")
    
    # Test 1: No image data
    print("\n🔍 Test: No image data...")
    try:
        response = requests.post(f'{BASE_URL}/predict', 
                               json={},
                               timeout=30)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 400:
            print(f"✅ Correctly rejected empty request")
        else:
            print(f"❌ Should have rejected empty request")
            
    except Exception as e:
        print(f"❌ Error test failed: {e}")
    
    # Test 2: Invalid base64
    print("\n🔍 Test: Invalid base64...")
    try:
        response = requests.post(f'{BASE_URL}/predict', 
                               json={'image_data': 'invalid_base64_data'},
                               timeout=30)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 400:
            print(f"✅ Correctly rejected invalid base64")
        else:
            print(f"❌ Should have rejected invalid base64")
            
    except Exception as e:
        print(f"❌ Invalid base64 test failed: {e}")
    
    # Test 3: Large file (if applicable)
    print("\n🔍 Test: Large file handling...")
    try:
        # Create a large image
        large_image = Image.new('RGB', (4000, 4000), color=(220, 180, 140))
        
        img_bytes = io.BytesIO()
        large_image.save(img_bytes, format='JPEG', quality=90)
        img_bytes.seek(0)
        
        files = {'image': ('large_test.jpg', img_bytes, 'image/jpeg')}
        
        response = requests.post(f'{BASE_URL}/predict', 
                               files=files,
                               timeout=60)  # Longer timeout for large file
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Large file handled successfully")
            print(f"   Prediction: {result.get('predicted_class', 'unknown')}")
        elif response.status_code == 413:
            print(f"✅ Correctly rejected large file (413 Payload Too Large)")
        else:
            print(f"⚠️ Unexpected response for large file: {response.text}")
            
    except Exception as e:
        print(f"❌ Large file test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting comprehensive image upload tests...")
    
    # Main upload tests
    test_upload_methods()
    
    # Format tests
    test_image_formats()
    
    # Error handling tests
    test_error_cases()
    
    print("\n" + "="*60)
    print("🎉 Upload tests completed!")
    print("\nTo test with cloud deployment, change BASE_URL to:")
    print("https://scan-skin-1065584510816.us-central1.run.app")
