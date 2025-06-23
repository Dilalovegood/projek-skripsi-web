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
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_image(image_data, is_base64=False):
    """Save uploaded image and return filename"""
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"scan_{timestamp}_{unique_id}.jpg"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        if is_base64:
            # Handle base64 image
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
        else:
            # Handle file upload
            image = Image.open(image_data)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize image for storage (optional, to save space)
        image.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        # Save image
        image.save(filepath, 'JPEG', quality=85)
        
        return filename
        
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

@scan_bp.route('/predict', methods=['POST'])
def predict():
    """Handle image prediction"""
    try:
        saved_filename = None
        
        # Check if image is uploaded via file or base64
        if 'image' in request.files:
            # File upload
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if file and allowed_file(file.filename):
                # Save uploaded image
                saved_filename = save_uploaded_image(file.stream)
                
                # Reset file pointer for prediction
                file.stream.seek(0)
                
                # Get prediction
                result = get_prediction(Image.open(file.stream))
                
            else:
                return jsonify({'error': 'Invalid file type'}), 400
                
        elif 'image_data' in request.json:
            # Base64 image data (from camera)
            image_data = request.json['image_data']
            
            # Save captured image
            saved_filename = save_uploaded_image(image_data, is_base64=True)
            
            # Get prediction
            result = get_prediction(image_data)
        else:
            return jsonify({'error': 'No image provided'}), 400
        
        if result.get('error'):
            return jsonify(result), 500
        
        # Store result in session for result page
        session['last_prediction'] = {
            'predicted_class': result['predicted_class'],
            'confidence': result['confidence'],
            'probabilities': result['probabilities'],
            'image_filename': saved_filename,
            'timestamp': datetime.now().isoformat()
        }
        
        # Return result with image filename
        result['image_filename'] = saved_filename
        return jsonify(result)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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