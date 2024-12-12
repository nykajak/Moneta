# Imports
from flask import render_template
from api import app

# Route that reroutes user to their profile page if logged in, the about page if not.
# Tested OK - Gamma
@app.route("/")
def home():
    return render_template("base_templates/home.html")
