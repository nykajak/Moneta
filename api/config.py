import os
base_dir = os.path.abspath(os.path.dirname(__file__)) # Constructs path for you.

# Base class - Do not use
class Config:
    DEBUG = False
    SQLITE_DB_DIR = None
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# Development class
class LocalConfig(Config):
    SQLITE_DB_DIR = os.path.join(base_dir, "../instance")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(SQLITE_DB_DIR,"test.db")
    DEBUG = True
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")