import os
base_dir = os.path.abspath(os.path.dirname(__file__))

class Config:
    DEBUG = False
    SQLITE_DB_DIR = None
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class LocalConfig(Config):
    SQLITE_DB_DIR = os.path.join(base_dir, "../instance")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(SQLITE_DB_DIR,"test.db")
    DEBUG = True
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    SECURITY_PASSWORD_HASH = "bcrypt"
    SECURITY_PASSWORD_SALT = os.getenv("FLASK_SECRET_SALT")
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_UNAUTHORISED_VIEW = None