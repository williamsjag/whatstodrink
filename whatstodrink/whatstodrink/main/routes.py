from flask import render_template, request, session, Blueprint
from whatstodrink.__init__ import db
from sqlalchemy import text
from whatstodrink.main.forms import SettingsForm
from flask_login import current_user, login_required

main = Blueprint('main', __name__)

# About and Homepage

@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/", methods=["GET", "POST"])
@main.route("/home", methods=["GET", "POST"])
@login_required
def index():

    form = SettingsForm()

    if request.method == "GET":
        defaults = session.get("defaults")
        if defaults is None:
            session['defaults'] = current_user.default_cocktails
            defaults = session['defaults']
        return render_template(
            "index.html", defaults=defaults, form=form
        )
    elif request.method == "POST":
        cocktails = request.form.get('cocktailswitch')

        if cocktails:
            # Update database defaults for next login
            cocktailupdate = text("UPDATE users SET default_cocktails = 'on' WHERE id = :user_id")
            db.session.execute(cocktailupdate, {"user_id": current_user.id})
            db.session.commit()

            # Update current session defaults
            session["defaults"] = 'on'

        else:
            # Update database defaults for next login
            cocktailupdate = text("UPDATE users SET default_cocktails = '' WHERE id = :user_id")
            db.session.execute(cocktailupdate, {"user_id": current_user.id})
            db.session.commit()

            # Update current session defaults
            session["defaults"] = ''

        return render_template("index.html", form=form)