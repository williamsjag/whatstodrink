from flask import render_template, Blueprint
from flask_login import current_user, login_required
from whatstodrink.helpers import update_cocktail_recipes

main = Blueprint('main', __name__)

# About and Homepage

@main.route("/about")
def about():
    update_cocktail_recipes()
    return render_template("about.html")


@main.route("/", methods=["GET", "POST"])
@main.route("/home", methods=["GET", "POST"])
@login_required
def index():

    return render_template("index.html")