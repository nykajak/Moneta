import os
from flask import Flask
from moneta.config import LocalConfig
from moneta.database import db
from flask_bcrypt import Bcrypt
# from flask_security.models import fsqla_v3 as fsqla

app = None

def create_app():
    app = Flask(__name__,template_folder="templates")
    environment = os.getenv('ENV','development')
    if environment == 'production':
        raise Exception("No production environment set up yet.")
    
    elif environment == 'testing':
        raise Exception("No testing environment set up yet.")
    
    elif environment == 'development':
        print("Configuring from local development environment")
        app.config.from_object(LocalConfig)

    else:
        raise Exception("Invalid environment specified!")
    

    db.init_app(app)
    app.app_context().push()
    bcrypt = Bcrypt()
    return app,bcrypt

app,bcrypt = create_app()
from moneta import routes