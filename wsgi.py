import os
from app import create_app

application = create_app()

if __name__ == '__main__':
    # Cloud Run menyediakan PORT melalui environment variable
    port = int(os.environ.get('PORT', 8080))
    application.run(debug=False, host='0.0.0.0', port=port)
