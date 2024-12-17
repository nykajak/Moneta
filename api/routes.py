# Imports
from flask import request,render_template,flash,redirect,url_for
from api import app,db,bcrypt,login_manager
from api.forms import *
from api.models import *
from flask_login import login_user,logout_user,current_user
from functools import wraps
from sqlalchemy import insert,func
from datetime import timedelta,datetime

## Utility functions!

# Helper function called internally to login correct user.
# Tested OK - Gamma
@login_manager.user_loader
def load_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    app.logger.info(f"User {user.username} was loaded!")
    return user

# Helper function called internally to display content for pages that do not exist.
# Tested OK - Gamma
@app.errorhandler(404)
def page_not_found(e):
    if not current_user.is_anonymous:
        app.logger.warning(f"The page with url: {request.url} was requested by user: {current_user.username}")
    else:
        app.logger.warning(f"The page with url: {request.url} was requested by an anonymous user")
    return "Page not found",404

# Helper wrapper to ensure that only librarians can access certain pages.
# Tested OK - Gamma
def librarian_required(fun):
    @wraps(fun)
    def inner(*args,**kwargs):
        if not current_user.is_anonymous and current_user.is_librarian:
            return fun(*args,**kwargs)
        else:
            if current_user.is_anonymous:
                app.logger.warning(f"Unauthorised anonymous user tried to access librarian endpoint: {fun.__name__}, {args=}, {kwargs=}")
            else:
                app.logger.warning(f"Unauthorised user ({current_user.username}) tried to access librarian endpoint: {fun.__name__}, {args=}, {kwargs=}")
            return app.login_manager.unauthorized()
    return inner

# Helper wrapper to ensure that only normal users can access certain pages.
# Tested OK - Gamma
def normal_user_required(fun):
    @wraps(fun)
    def inner(*args,**kwargs):
        if not current_user.is_anonymous and not current_user.is_librarian:
            return fun(*args,**kwargs)
        else:
            if current_user.is_anonymous:
                app.logger.warning(f"Unauthorised anonymous user tried to access user endpoint: {fun.__name__}, {args=}, {kwargs=}")
            else:
                app.logger.warning(f"Unauthorised librarian ({current_user.username}) tried to access user endpoint: {fun.__name__}, {args=}, {kwargs=}")
            return app.login_manager.unauthorized()
    return inner    

# Route that reroutes user to their profile page if logged in, the about page if not.
# Tested OK - Gamma
@app.route("/")
def home():
    return render_template("base_templates/home.html")

@app.route("/login")
def login():
    return render_template("base_templates/home.html")

@app.route("/register")
def register():
    return render_template("base_templates/home.html")