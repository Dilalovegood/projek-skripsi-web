from flask import Flask, render_template
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize model
    if app.config['MODEL_PATH'] and os.path.exists(app.config['MODEL_PATH']):
        from app.service.model_handler import initialize_model
        if initialize_model(app.config['MODEL_PATH']):
            print(f"✅ Model initialized successfully from: {app.config['MODEL_PATH']}")
        else:
            print("❌ Failed to initialize model")
    else:
        print("⚠️  No model file found. Please place your model in the models/ directory")
        if app.config['MODEL_DIR']:
            print(f"📁 Looking in: {app.config['MODEL_DIR']}")
    
    # Register blueprints
    from app.routes.scan import scan_bp
    app.register_blueprint(scan_bp)

    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/scantype')
    def skinType():
        return render_template('skintype.html')

    return app