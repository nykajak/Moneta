from flask import request,render_template,flash,redirect,url_for,session
from moneta import app,db,bcrypt,login_manager
from moneta.forms import MyLoginForm,MyRegistrationForm
from moneta.models import User
from flask_login import login_user,logout_user,login_required,current_user

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()

@app.route("/")
def home():
    return render_template("home.html",user=current_user)

@app.route("/test")
def test():
    return render_template("test.html",user = current_user)

@app.route("/login",methods=['GET','POST'])
def login():
    form = MyLoginForm()

    if form.validate_on_submit():
        app.logger.info("Login form validated!")

        u = User.query.filter_by(email=form.email.data).first()
        app.logger.debug("User query processed!")

        if u and bcrypt.check_password_hash(u.password,form.password.data):
            app.logger.debug("Successful login!")
            res = login_user(u)
            app.logger.debug(f"Result of logging in is: {res}")

            next = request.args.get('next')
            return redirect(next or url_for('home'))

        else:
            if not u:
                app.logger.debug("No such user!")
                flash("No such user found!",category="danger")
            else:
                app.logger.debug("User provided incorrect password!")
                flash("Incorrect password!",category="danger")

    return render_template("login.html",login_user_form = form)


@app.route("/register",methods=['GET','POST'])
def register():
    form = MyRegistrationForm()

    if form.validate_on_submit():
        app.logger.info("Register form validated!")

        hashed_password = bcrypt.generate_password_hash(form.password.data)
        u = User(username=form.username.data,email=form.email.data,password=hashed_password)
        app.logger.debug("User query processed!")

        flag = 0
        try:
            db.session.add(u)
            db.session.commit()
            flag = 1

        except Exception as E:
            failed = E.args[0][56:]
            if failed == 'email':
                app.logger.debug("User not created as email already exists!")
                flash("Email already in use",category='danger')
            elif failed == 'username':
                app.logger.debug("User not created as username already exists!")
                flash("Username already in use",category='danger')
                

        if flag:
            app.logger.debug("User created!")
            res = login_user(u)
            app.logger.debug(f"Result of logging in is: {res}")
            app.logger.debug("User logged in!")

            next = request.args.get('next')
            return redirect(next or url_for('home'))
        else:
            pass    

    return render_template("register.html",register_user_form = form)

@app.route("/logout")
def logout():
    logout_user()
    app.logger.debug("User logged out!")
    return redirect(url_for('home'))
    

@app.errorhandler(404)
def page_not_found(e):
    app.logger.critical("Expected page does not exist!")
    return "Page not found",404