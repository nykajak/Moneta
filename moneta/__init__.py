import os
from flask import Flask
from moneta.config import LocalConfig
from moneta.database import db
from moneta.forms import MyLoginForm,MyRegistrationForm
from flask_security import Security, SQLAlchemySessionUserDatastore, SQLAlchemyUserDatastore
from moneta.models import User,Role
from flask_security.models import fsqla_v3 as fsqla

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

    user_datastore = SQLAlchemyUserDatastore(db,User,Role)
    app.security = Security(app,user_datastore, login_form=MyLoginForm,register_form=MyRegistrationForm) 
    fsqla.FsModels.set_db_info(db)

    return app

app = create_app()
from moneta import routes