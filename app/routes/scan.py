import os
import base64
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app, session
from werkzeug.utils import secure_filename
from PIL import Image
import io
from app.service.model_handler import get_prediction

scan_bp = Blueprint('scan', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    if not filename:
        return False
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_file_extension(filename):
    """Get file extension from filename"""
    if not filename or '.' not in filename:
        return None
    return filename.rsplit('.', 1)[1].lower()

def save_uploaded_image(image_data, is_base64=False):
    """Save uploaded image and return filename"""
    try:
        # Ensure upload directory exists
        upload_dir = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
            print(f"📁 Created upload directory: {upload_dir}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"scan_{timestamp}_{unique_id}.jpg"
        filepath = os.path.join(upload_dir, filename)
        
        print(f"💾 Saving image to: {filepath}")
        
        if is_base64:
            # Handle base64 image
            if isinstance(image_data, str):
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',')[1]
                
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
            else:
                raise ValueError("Base64 data must be string")
        else:
            # Handle file upload or BytesIO
            if isinstance(image_data, io.BytesIO):
                image_data.seek(0)  # Reset position
                image = Image.open(image_data)
            elif hasattr(image_data, 'read'):
                # For file streams from request.files
                image_data.seek(0)  # Reset position
                image = Image.open(image_data)
            elif hasattr(image_data, 'stream'):
                # For werkzeug FileStorage objects
                image_data.stream.seek(0)
                image = Image.open(image_data.stream)
            else:
                # Direct PIL Image or other formats
                image = Image.open(image_data)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get original size
        original_size = image.size
        print(f"📏 Original image size: {original_size}")
        
        # Resize image for storage (optional, to save space)
        max_size = 1024
        if max(original_size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            print(f"📐 Resized image to: {image.size}")
        
        # Save image with good quality
        image.save(filepath, 'JPEG', quality=90, optimize=True)
        
        # Check file was saved successfully
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✅ Image saved successfully: {filename} ({file_size} bytes)")
            return filename
        else:
            print(f"❌ Failed to save image: {filepath}")
            return None
        
    except Exception as e:
        print(f"❌ Error saving image: {e}")
        import traceback
        traceback.print_exc()
        return None

@scan_bp.route('/predict', methods=['POST'])
def predict():
    """Predict skin type from uploaded image - supports multiple formats"""
    try:
        print(f"🔄 Received prediction request")
        print(f"Content-Type: {request.content_type}")
        print(f"Headers: {dict(request.headers)}")
        
        image = None
        image_source = None
        
        # Method 1: JSON dengan base64 (Content-Type: application/json)
        if request.is_json:
            try:
                json_data = request.get_json()
                print(f"📄 JSON data keys: {list(json_data.keys()) if json_data else 'None'}")
                
                if json_data and 'image_data' in json_data:
                    image_data = json_data['image_data']
                    print(f"📄 Processing JSON base64 data (length: {len(image_data)})")
                    
                    # Handle data URL format
                    if image_data.startswith('data:image'):
                        image_data = image_data.split(',')[1]
                    
                    # Decode base64
                    image_bytes = base64.b64decode(image_data)
                    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
                    image_source = "json_base64"
                    
                    # Save the image
                    saved_filename = save_uploaded_image(json_data['image_data'], is_base64=True)
                    
            except Exception as e:
                print(f"❌ Error processing JSON: {e}")
                import traceback
                traceback.print_exc()
        
        # Method 2: Form data dengan file upload (Content-Type: multipart/form-data)
        elif 'multipart/form-data' in str(request.content_type):
            print(f"📁 Processing multipart form data")
            print(f"Form keys: {list(request.form.keys())}")
            print(f"Files keys: {list(request.files.keys())}")
            
            # Check for file upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    print(f"📁 Processing uploaded file: {file.filename}")
                    try:
                        # Process the image
                        image = Image.open(file.stream).convert('RGB')
                        image_source = "file_upload"
                        
                        # Save the image - pass the file object directly
                        saved_filename = save_uploaded_image(file, is_base64=False)
                        
                    except Exception as e:
                        print(f"❌ Error processing uploaded file: {e}")
                        return jsonify({
                            'success': False,
                            'error': f'Invalid image file: {str(e)}',
                            'image_source': 'file_upload_error'
                        }), 400
                else:
                    print(f"❌ Invalid file upload: {file.filename if file else 'No file'}")
                    return jsonify({
                        'success': False,
                        'error': 'No valid image file provided',
                        'image_source': 'file_upload_invalid'
                    }), 400
            
            # Check for base64 in form data
            elif 'image_data' in request.form:
                image_data = request.form['image_data']
                print(f"📝 Processing form base64 data (length: {len(image_data)})")
                
                try:
                    if image_data.startswith('data:image'):
                        image_data = image_data.split(',')[1]
                    
                    image_bytes = base64.b64decode(image_data)
                    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
                    image_source = "form_base64"
                    
                    # Save the image
                    saved_filename = save_uploaded_image(request.form['image_data'], is_base64=True)
                    
                except Exception as e:
                    print(f"❌ Error processing form base64: {e}")
                    return jsonify({
                        'success': False,
                        'error': f'Invalid base64 image data: {str(e)}',
                        'image_source': 'form_base64_error'
                    }), 400
        
        # Method 3: Raw form data (Content-Type: application/x-www-form-urlencoded)
        elif 'application/x-www-form-urlencoded' in str(request.content_type):
            print(f"📝 Processing URL-encoded form data")
            print(f"Form keys: {list(request.form.keys())}")
            
            if 'image_data' in request.form:
                image_data = request.form['image_data']
                print(f"📝 Processing URL-encoded base64 data (length: {len(image_data)})")
                
                try:
                    if image_data.startswith('data:image'):
                        image_data = image_data.split(',')[1]
                    
                    image_bytes = base64.b64decode(image_data)
                    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
                    image_source = "urlencoded_base64"
                    
                    # Save the image
                    saved_filename = save_uploaded_image(request.form['image_data'], is_base64=True)
                    
                except Exception as e:
                    print(f"❌ Error processing URL-encoded base64: {e}")
                    return jsonify({
                        'success': False,
                        'error': f'Invalid URL-encoded image data: {str(e)}',
                        'image_source': 'urlencoded_error'
                    }), 400
        
        # Method 4: Raw binary data (Content-Type: image/*)
        elif request.content_type and request.content_type.startswith('image/'):
            print(f"🖼️ Processing raw image data")
            try:
                image_data = request.get_data()
                image = Image.open(io.BytesIO(image_data)).convert('RGB')
                image_source = "raw_image"
                
                # Save the image
                saved_filename = save_uploaded_image(io.BytesIO(image_data), is_base64=False)
                
            except Exception as e:
                print(f"❌ Error processing raw image: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Invalid raw image data: {str(e)}',
                    'image_source': 'raw_image_error'
                }), 400
        
        # Method 5: Try to parse any remaining data as JSON
        else:
            print(f"🔄 Trying to parse as JSON regardless of content-type")
            try:
                # Try to get JSON data even if content-type is wrong
                raw_data = request.get_data(as_text=True)
                if raw_data:
                    import json
                    json_data = json.loads(raw_data)
                    
                    if 'image_data' in json_data:
                        image_data = json_data['image_data']
                        print(f"📄 Processing fallback JSON base64 data (length: {len(image_data)})")
                        
                        if image_data.startswith('data:image'):
                            image_data = image_data.split(',')[1]
                        
                        image_bytes = base64.b64decode(image_data)
                        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
                        image_source = "fallback_json"
                        
                        # Save the image
                        saved_filename = save_uploaded_image(json_data['image_data'], is_base64=True)
                        
            except Exception as e:
                print(f"❌ Fallback JSON parsing failed: {e}")
        
        # Validate image was successfully loaded
        if image is None:
            print("❌ No image found in request")
            return jsonify({
                'success': False,
                'error': 'No image provided or unsupported format',
                'debug': {
                    'content_type': str(request.content_type),
                    'form_keys': list(request.form.keys()),
                    'files_keys': list(request.files.keys()),
                    'is_json': request.is_json,
                    'data_length': len(request.get_data()) if request.get_data() else 0
                }
            }), 400
        
        print(f"✅ Image loaded from {image_source}: {image.size}")
        if saved_filename:
            print(f"✅ Image saved as: {saved_filename}")
        
        # Make prediction
        result = get_prediction(image)
        
        # Check if prediction was successful
        if 'error' in result:
            print(f"❌ Prediction failed: {result['error']}")
            return jsonify({
                'success': False,
                'error': result['error'],
                'predicted_class': result.get('predicted_class', 'normal'),
                'confidence': result.get('confidence', 0.5),
                'probabilities': result.get('probabilities', {}),
                'image_source': image_source,
                'image_filename': saved_filename
            }), 500
        else:
            print(f"✅ Prediction successful: {result['predicted_class']}")
            
            # Store result in session for result page
            session['last_prediction'] = {
                'predicted_class': result['predicted_class'],
                'confidence': result['confidence'],
                'probabilities': result['probabilities'],
                'image_filename': saved_filename,
                'image_source': image_source,
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'predicted_class': result['predicted_class'],
                'confidence': result['confidence'],
                'probabilities': result['probabilities'],
                'image_source': image_source,
                'image_filename': saved_filename
            })
            
    except Exception as e:
        print(f"❌ Error in predict route: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}',
            'predicted_class': 'normal',
            'confidence': 0.5,
            'probabilities': {'berminyak': 0.25, 'kering': 0.25, 'kombinasi': 0.25, 'normal': 0.25}
        }), 500
    

@scan_bp.route('/result')
def result():
    """Show prediction result page"""
    # Try to get data from session first
    prediction_data = session.get('last_prediction')
    
    if prediction_data:
        prediction = prediction_data['predicted_class']
        confidence = prediction_data['confidence']
        image_filename = prediction_data.get('image_filename')
    else:
        # Fallback to query params
        prediction = request.args.get('prediction', 'normal')
        confidence = float(request.args.get('confidence', 0.85))
        image_filename = request.args.get('image_filename')
    
    # Skin type information dengan data yang lebih lengkap
    skin_info = {
        'normal': {
            'title': 'Normal',
            'description': 'Kulit normal memiliki keseimbangan yang baik antara minyak dan kelembaban. Kulit terlihat sehat, halus, dan jarang mengalami masalah.',
            'characteristics': [
                'Pori-pori kecil dan tidak terlalu terlihat',
                'Tekstur kulit halus dan lembut',
                'Tidak terlalu berminyak atau kering',
                'Jarang mengalami jerawat atau iritasi',
                'Warna kulit merata dan terlihat sehat'
            ],
            'care_tips': [
                'Gunakan pembersih yang lembut dan tidak mengiritasi',
                'Aplikasikan pelembab sesuai kebutuhan kulit',
                'Gunakan sunscreen dengan SPF minimal 30 setiap hari',
                'Lakukan eksfoliasi ringan 1-2 kali seminggu'
            ]
        },
        'berminyak': {
            'title': 'Berminyak',
            'description': 'Kulit berminyak memproduksi sebum berlebih yang dapat menyebabkan kilap, pori-pori besar, dan rentan terhadap jerawat.',
            'characteristics': [
                'Pori-pori besar dan terlihat jelas',
                'Wajah terlihat mengkilap terutama di T-zone',
                'Mudah berjerawat dan berkomedo',
                'Makeup mudah luntur atau tergeser',
                'Tekstur kulit agak kasar'
            ],
            'care_tips': [
                'Gunakan pembersih yang mengontrol minyak tanpa over-cleansing',
                'Pilih pelembab yang oil-free dan tidak comedogenic',
                'Gunakan toner dengan salicylic acid untuk mengecilkan pori',
                'Lakukan eksfoliasi teratur dengan BHA'
            ]
        },
        'kering': {
            'title': 'Kering',
            'description': 'Kulit kering kekurangan minyak alami dan kelembaban, sehingga terasa kencang dan mudah mengelupas.',
            'characteristics': [
                'Kulit terasa kencang terutama setelah dibersihkan',
                'Mudah mengelupas dan bersisik',
                'Pori-pori hampir tidak terlihat',
                'Mudah iritasi dan sensitif',
                'Garis-garis halus lebih terlihat'
            ],
            'care_tips': [
                'Gunakan pembersih yang lembut dan melembabkan',
                'Aplikasikan pelembab yang kaya akan ceramide dan hyaluronic acid',
                'Hindari produk berbasis alkohol atau parfum',
                'Gunakan humidifier di ruangan untuk menambah kelembaban'
            ]
        },
        'kombinasi': {
            'title': 'Kombinasi',
            'description': 'Kulit kombinasi memiliki area berminyak (biasanya T-zone) dan area kering atau normal di bagian lain wajah.',
            'characteristics': [
                'T-zone (dahi, hidung, dagu) berminyak',
                'Pipi cenderung normal atau kering',
                'Pori-pori besar di area T-zone',
                'Jerawat sering muncul di T-zone',
                'Membutuhkan perawatan berbeda untuk area yang berbeda'
            ],
            'care_tips': [
                'Gunakan produk yang berbeda untuk area yang berbeda',
                'Fokus kontrol minyak di T-zone dengan salicylic acid',
                'Berikan kelembaban ekstra di area pipi yang kering',
                'Gunakan masker clay khusus untuk T-zone saja'
            ]
        }
    }
    
    current_skin_info = skin_info.get(prediction, skin_info['normal'])
    
    return render_template('result.html', 
                         prediction=prediction,
                         confidence=confidence,
                         skin_info=current_skin_info,
                         image_filename=image_filename)