from flask import Flask
from backend.models import db
app  = None

def initial_Setup():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    db.init_app(app)
    app.app_context().push()
    return
    
initial_Setup()

from backend.routes import *

if __name__ == '__main__':
    app.run(debug=True)

# This is a simple Flask application setup.