# Imports
from flask import request,render_template,flash,redirect,url_for
from api import app,db,bcrypt,login_manager
from api.forms import *
from api.models import *
from flask_login import login_user,logout_user,current_user
from functools import wraps
from sqlalchemy import insert,func
from datetime import timedelta,datetime

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