import sys
import os

project_home = '/home/kreavamy/scanskin'  # sesuaikan USERNAME
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['FLASK_ENV'] = 'production'

from wsgi import app as application  # karena app = Flask(__name__) ada di wsgi.py
