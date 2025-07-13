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
    return filename and '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_image(image):
    """Save uploaded image and return filename"""
    try:
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"scan_{timestamp}_{unique_id}.jpg"
        filepath = os.path.join(upload_dir, filename)
        
        # Convert to RGB and save
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too large
        if max(image.size) > 1024:
            image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        
        image.save(filepath, 'JPEG', quality=90)
        return filename if os.path.exists(filepath) else None
        
    except Exception as e:
        print(f"❌ Error saving image: {e}")
        return None

@scan_bp.route('/predict', methods=['POST'])
def predict():
    """Predict skin type from uploaded image"""
    try:
        image = None
        
        # Handle JSON with base64
        if request.is_json:
            json_data = request.get_json()
            if json_data and 'image_data' in json_data:
                image_data = json_data['image_data']
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',')[1]
                
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
        
        # Handle file upload
        elif 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                image = Image.open(file.stream)
        
        # Handle form base64
        elif 'image_data' in request.form:
            image_data = request.form['image_data']
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
        
        if not image:
            return jsonify({
                'success': False,
                'error': 'No valid image provided'
            }), 400
        
        # Save image
        saved_filename = save_uploaded_image(image)
        
        # Make prediction
        result = get_prediction(image)
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error'],
                'predicted_class': result.get('predicted_class', 'normal'),
                'confidence': result.get('confidence', 0.5)
            }), 500
        
        # Store in session
        session['last_prediction'] = {
            'predicted_class': result['predicted_class'],
            'confidence': result['confidence'],
            'probabilities': result['probabilities'],
            'image_filename': saved_filename,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'predicted_class': result['predicted_class'],
            'confidence': result['confidence'],
            'probabilities': result['probabilities'],
            'image_filename': saved_filename
        })
        
    except Exception as e:
        print(f"❌ Error in predict: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}',
            'predicted_class': 'normal',
            'confidence': 0.5
        }), 500

@scan_bp.route('/result')
def result():
    """Show prediction result page"""
    prediction_data = session.get('last_prediction')
    
    if not prediction_data:
        flash('No prediction found. Please scan your skin first.', 'error')
        return redirect(url_for('main.scantype'))
    
    prediction = prediction_data['predicted_class']
    confidence = prediction_data['confidence']
    image_filename = prediction_data.get('image_filename')
    
    # Skin type information
    skin_info_data = {
        'normal': {
            'title': 'Normal',
            'description': 'Kulit normal memiliki keseimbangan yang baik antara minyak dan kelembaban.',
            'characteristics': [
                'Pori-pori kecil dan tidak terlalu terlihat',
                'Tekstur kulit halus dan lembut',
                'Tidak terlalu berminyak atau kering',
                'Jarang mengalami jerawat atau iritasi'
            ],
            'cleanser': [
                'Rose Water (menenangkan, pH balance)',
                'Glycolic Acid (eksfoliasi ringan)',
                'Hyaluronic Acid (hidrasi)'
            ],
            'moisturizer': [
                'Ceramide untuk menjaga barrier kulit',
                'Hyaluronic Acid untuk hidrasi optimal',
                'Glycerin untuk kelembaban',
                'Peptides untuk regenerasi kulit',
                'Non-comedogenic formula'
            ],
            'sunscreen': [
                'Vitamin C, E, Niacinamide (antioksidan)',
                'Zinc Oxide / Titanium Dioxide (mineral sunscreen)',
                'Broad Spectrum SPF 30+'
            ]
        },
        'berminyak': {
            'title': 'Berminyak',
            'description': 'Kulit berminyak memproduksi sebum berlebih yang dapat menyebabkan kilap dan jerawat.',
            'characteristics': [
                'Pori-pori besar dan terlihat jelas',
                'Wajah terlihat mengkilap terutama di T-zone',
                'Mudah berjerawat dan berkomedo',
                'Makeup mudah luntur atau tergeser',
                'Tekstur kulit agak kasar'
            ],
            'cleanser': [
                'Niacinamide (kontrol minyak, pori, antiinflamasi)',
                'Salicylic Acid (eksfoliasi pori)',
                'Glycolic Acid (eksfoliasi sel mati)',
                'Hyaluronic Acid (melembapkan)'
            ],
            'moisturizer': [
                'Ceramide untuk memperbaiki barrier kulit',
                'Hyaluronic Acid untuk hidrasi tanpa berminyak',
                'Niacinamide untuk kontrol sebum',
                'Salicylic Acid untuk mencegah komedo'
            ],
            'sunscreen': [
                'Zinc Oxide atau Titanium Dioxide',
                'Non-comedogenic untuk mencegah jerawat'
            ]
        },
        'kering': {
            'title': 'Kering',
            'description': 'Kulit kering kekurangan minyak alami dan kelembaban.',
            'characteristics': [
                'Kulit terasa kencang terutama setelah dibersihkan',
                'Mudah mengelupas dan bersisik',
                'Pori-pori hampir tidak terlihat',
                'Mudah iritasi dan sensitif',
                'Garis-garis halus lebih terlihat'
            ],
            'cleanser': [
                'Glycerin (melembapkan)',
                'Vitamin E, Minyak Jojoba (melembapkan tanpa rasa berat)',
                'Urea (mengurangi kehilangan air)'
            ],
            'moisturizer': [
                'Ceramide untuk memperkuat skin barrier',
                'Shea Butter untuk nutrisi intensif',
                'Squalane untuk kelembaban mendalam',
                'Glycerin untuk hidrasi',
                'Panthenol untuk menenangkan kulit'
            ],
            'sunscreen': [
                'Sunscreen SPF 30+ dengan formula melembapkan',
                'Tambahan pelembap dalam sunscreen',
                'Hindari formula yang mengandung alkohol'
            ]
        },
        'kombinasi': {
            'title': 'Kombinasi',
            'description': 'Kulit kombinasi memiliki area berminyak dan area kering.',
            'characteristics': [
                'T-zone (dahi, hidung, dagu) berminyak',
                'Pipi cenderung normal atau kering',
                'Pori-pori besar di area T-zone',
                'Jerawat sering muncul di T-zone',
                'Membutuhkan perawatan berbeda untuk area yang berbeda'
            ],
            'cleanser': [
                'Mild surfaktan seperti Sodium Cocoyl Isethionate',
                'Sodium Lauroyl Methyl Isethionate',
                'Cocamidopropyl Betaine',
                'Decyl Glucoside untuk pembersihan lembut'
            ],
            'moisturizer': [
                'Ringan di T-zone, lebih kaya di area kering',
                'Niacinamide untuk kontrol minyak di T-zone',
                'Hyaluronic Acid untuk hidrasi seimbang',
                'Aloe Vera untuk menenangkan kulit'
            ],
            'sunscreen': [
                'Sunscreen non-comedogenic',
                'SPF minimal 30 dengan broad spectrum',
                'Tekstur ringan agar tidak berminyak di T-zone'
            ]
        }
    }
    
    current_skin_info = skin_info_data.get(prediction, skin_info_data['normal'])
    
    return render_template('result.html', 
                         prediction=prediction,
                         confidence=confidence,
                         skin_info=current_skin_info,
                         image_filename=image_filename)