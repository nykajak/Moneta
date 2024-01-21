from flask import request,render_template,flash
from moneta import app,db

@app.route("/test")
def test():
    return "Hello",200