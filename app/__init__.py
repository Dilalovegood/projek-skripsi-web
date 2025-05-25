from flask import Flask, render_template


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/scantype')
    def skinType():
        return render_template('skintype.html')
    
    @app.route('/result')
    def details():
        return render_template('single-skintype.html')

    return app
