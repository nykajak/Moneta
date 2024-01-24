from flask import request,render_template,flash,render_template_string,redirect
from moneta import app,db,bcrypt
from moneta.forms import MyLoginForm,MyRegistrationForm
from moneta.models import User

@app.route("/")
def test():
    return render_template("test.html")

@app.route("/login",methods=['GET','POST'])
def login():
    form = MyLoginForm()

    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data).first()
        if u and bcrypt.check_password_hash(u.password,form.password.data):
            print('Successful login!')
            # Login user code here!
            redirect('/',200)

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
        u = User(username=form.username.data,email=form.email.data,password=hashed_password,active=1)
        flag = 0
        try:
            db.session.add(u)
            db.session.commit()
            flag = 1
        except Exception as E:
            print(E)

        if flag:
            print("User created!")
            # Login code here!
            redirect('/',200)
        else:
            print("User not created!")
        

    return render_template("register.html",register_user_form = form)

@app.route("/logout")
def logout():
    pass
    

@app.errorhandler(404)
def page_not_found(e):
    return "Page not found",404