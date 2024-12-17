# Imports
import os
from flask import Flask
from api.config import LocalConfig
from api.database import db
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = None

# Setting up login manager
login_manager = LoginManager()

def create_app():
    #Creation of app.
    app = Flask(__name__,template_folder="templates")
    environment = os.getenv('ENV','development')

    #Configuring app
    if environment == 'production':
        raise Exception("No production environment set up yet.")
    
    elif environment == 'testing':
        raise Exception("No testing environment set up yet.")
    
    elif environment == 'development':
        print("Configuring from local development environment")
        app.config.from_object(LocalConfig)

    else:
        raise Exception("Invalid environment specified!")
    
    #Configuring db
    db.init_app(app)

    app.app_context().push()

    #Configuring hashing and security
    bcrypt = Bcrypt()
    return app,bcrypt

#Instantiating app and login manager
app,bcrypt = create_app()
login_manager.init_app(app)

#Importing all the routes
from api import routes