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

## Global user routes

# Route that renders the common login form
# Tested OK - Gamma
@app.route("/login",methods=['GET','POST'])
def login():
    form = MyLoginForm()

    if form.validate_on_submit():
        app.logger.info("Login form validated!")
        
        u = User.query.filter_by(email=form.email.data).first()
        app.logger.debug("User query processed!")

        if u and bcrypt.check_password_hash(u.password,form.password.data):
            res = login_user(u)
            if res:
                app.logger.info("Successful login!")
            else:
                app.logger.critical("Login failed.")

            # Remove expired books from user on login
            for b in current_user.borrowed:
                if (datetime.now() - b.b_date).days > 7:
                    obj = b
                    try:
                        db.session.add(Read(user_id = obj.user_id, book_id = obj.book_id))
                        db.session.commit()
                        app.logger.info(f"Added read relation: {obj.book.name} for user: {current_user.username}!")
                    except Exception:
                        db.session.rollback()
                    
                    Borrow.query.filter(Borrow.user_id == obj.user_id).filter(Borrow.book_id == obj.book_id).delete()
                    app.logger.info(f"Removed book: {obj.book.name} from user: {current_user.username}!")
                    db.session.commit()

            return redirect(url_for('home'))

        else:
            if not u:
                app.logger.debug(f"No user with email: {form.email.data}!")
                flash("No such user found!",category="danger")
            else:
                app.logger.debug("User provided incorrect password!")
                flash("Incorrect password!",category="danger")

    return render_template("anon_specific/login.html",login_user_form = form)

# Route that renders the registration form.
# Tested OK- Gamma
@app.route("/register",methods=['GET','POST'])
def register():
    form = MyRegistrationForm()

    if form.validate_on_submit():
        app.logger.info("Register form validated!")

        hashed_password = bcrypt.generate_password_hash(form.password.data)
        u = User(username=form.username.data,email=form.email.data,password=hashed_password)
        app.logger.debug("User query processed!")

        created = 0
        try:
            #Creating user.
            db.session.add(u)
            db.session.commit()
            created = 1

        except Exception as E:
            #Detecting which field repeated via the error message.
            failed = E.args[0][56:]
            if failed == 'email':
                app.logger.debug("User not created as email already exists!")
                flash("Email already in use",category='danger')
            elif failed == 'username':
                app.logger.debug("User not created as username already exists!")
                flash("Username already in use",category='danger')
                

        if created:
            app.logger.debug(f"User created with username:{form.username.data}!")
            res = login_user(u)
            if res:
                app.logger.info("User logged in!")
            else:
                app.logger.critical("Login failed.")

            return redirect(url_for('home'))

    return render_template("anon_specific/register.html",register_user_form = form)

# Logout route.
# Tested OK- Gamma
@app.route("/logout")
def logout():
    curr_name = current_user.username
    res = logout_user()
    if res:
        app.logger.debug(f"User {curr_name} logged out!")
    else:
        app.logger.critical("Logout failed.")
    return redirect(url_for('home'))
