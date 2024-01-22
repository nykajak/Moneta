from flask import request,render_template,flash,render_template_string
from moneta import app,db
from moneta.forms import MyLoginForm,MyRegistrationForm
from flask_security import auth_required

@app.route("/test")
@auth_required()
def test():
    return render_template_string("Hello {{ current_user.email }}")

@app.route("/dashboard",methods=['GET','POST'])
def dashboard():
    if request.method == "GET":
        return "Hi"
    else:
        return f""
    

@app.errorhandler(404)
def page_not_found(e):
    return "Page not found",404