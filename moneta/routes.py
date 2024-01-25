from flask import request,render_template,flash,redirect,url_for,session
from moneta import app,db,bcrypt,login_manager
from moneta.forms import MyLoginForm,MyRegistrationForm
from moneta.models import User
from flask_login import login_user,logout_user,login_required,current_user

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()

@app.route("/")
def main():
    return render_template("test.html")

@app.route("/test")
@login_required
def test():
    return render_template("test.html",user = current_user)

@app.route("/login",methods=['GET','POST'])
def login():
    form = MyLoginForm()

    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data).first()
        if u and bcrypt.check_password_hash(u.password,form.password.data):
            print('Successful login!')
            print(login_user(u))

            next = request.args.get('next')
            return redirect(next or url_for('test'))

        else:
            if not u:
                print("No such user!")
            else:
                print("Incorrect password!")

    return render_template("login.html",login_user_form = form)


@app.route("/register",methods=['GET','POST'])
def register():
    form = MyRegistrationForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        u = User(username=form.username.data,email=form.email.data,password=hashed_password)
        flag = 0
        try:
            db.session.add(u)
            db.session.commit()
            flag = 1
        except Exception as E:
            print(E)

        if flag:
            print("User created!")
            print(login_user(u))

            next = request.args.get('next')
            return redirect(next or url_for('test'))
        else:
            print("User not created!")
        

    return render_template("register.html",register_user_form = form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect('test')
    

@app.errorhandler(404)
def page_not_found(e):
    return "Page not found",404