from flask import Flask, render_template
import os
import threading

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize model in background thread to avoid blocking startup
    def initialize_model_async():
        try:
            # Initialize model
            if os.path.exists(app.config['MODEL_PATH']):
                from app.service.model_handler import initialize_model
                if initialize_model(app.config['MODEL_PATH']):
                    print(f"✅ Model initialized successfully from: {app.config['MODEL_PATH']}")
                else:
                    print("❌ Failed to initialize model")
            else:
                print(f"⚠️ No model file found at: {app.config['MODEL_PATH']}")
        except Exception as e:
            print(f"❌ Error initializing model: {e}")
    
    # Start model initialization in background
    model_thread = threading.Thread(target=initialize_model_async)
    model_thread.daemon = True
    model_thread.start()
    
    # Register blueprints
    from app.routes.scan import scan_bp
    app.register_blueprint(scan_bp)

    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/scantype')
    def skinType():
        return render_template('skintype.html')
    
    @app.route('/health')
    def health():
        from app.service.model_handler import is_model_loaded
        
        model_status = "loaded" if is_model_loaded() else "not_loaded"
        status = "healthy" if is_model_loaded() else "unhealthy"
        
        return {
            'status': status,
            'model': model_status,
            'message': 'Model loaded successfully' if is_model_loaded() else 'Model not initialized'
        }, 200 if is_model_loaded() else 503

    return app