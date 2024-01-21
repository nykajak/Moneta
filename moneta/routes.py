from flask import request,render_template,flash
from moneta import app,db

@app.route("/test")
def test():
    return render_template("test.html")