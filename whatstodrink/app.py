import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, union, text
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
import time


# Configure application
app = Flask(__name__)



# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure DB connection in SQLAlchemy and Python classes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///whatstodrink.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db2 = SQLAlchemy(app)


class User(db2.Model):
    __tablename__ = 'users'

    id = db2.Column(db2.Integer, primary_key=True, nullable=False, autoincrement=True)
    username = db2.Column(db2.String(50), nullable=False, unique=True)
    hash = db2.Column(db2.String(100), nullable=False)
    default_cocktails = db2.Column(db2.Integer, default="on")

    cocktails = db2.relationship('Cocktail', backref='users')
    common_stock = db2.relationship('CommonStock', backref='users')

class Amount(db2.Model):
    __tablename__ = 'amounts'

    cocktail_id = db2.Column(db2.Integer, db2.ForeignKey('cocktails.id'), primary_key=True)
    amount = db2.Column(db2.String(50))
    ingredient_id = db2.Column(db2.Integer, primary_key=True)
    user_id = db2.Column(db2.Integer, db2.ForeignKey('users.id'), primary_key=True)
    ingredient_source = db2.Column(db2.String(50), primary_key=True)

    

class Cocktail(db2.Model):
    __tablename__ = 'cocktails'

    id = db2.Column(db2.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db2.Column(db2.String(50), nullable=False)
    build = db2.Column(db2.String(1000))
    source = db2.Column(db2.String(50))
    user_id = db2.Column(db2.Integer, db2.ForeignKey('users.id'), nullable=False)
    family = db2.Column(db2.String(50), default="Orphans")
    



class Ingredient(db2.Model):
    __tablename__ = 'ingredients'

    id = db2.Column(db2.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db2.Column(db2.String(50), nullable=False)
    type = db2.Column(db2.String(50))
    stock = db2.Column(db2.Integer)
    user_id = db2.Column(db2.Integer)
    short_name = db2.Column(db2.String(50))
    notes = db2.Column(db2.String(1000))

    

class CommonAmount(db2.Model):
    __tablename__ = 'common_amounts'

    cocktail_id = db2.Column(db2.Integer, db2.ForeignKey('common_cocktails.id'), primary_key=True)
    amount = db2.Column(db2.String(50))
    ingredient_id = db2.Column(db2.Integer, db2.ForeignKey('common_ingredients.id'), primary_key=True)


class CommonIngredient(db2.Model):
    __tablename__ = 'common_ingredients'

    id = db2.Column(db2.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db2.Column(db2.String(50), nullable=False)
    type = db2.Column(db2.String(50))
    short_name = db2.Column(db2.String(50))
    notes = db2.Column(db2.String(1000))


class CommonStock(db2.Model):
    __tablename__ = 'common_stock'

    ingredient_id = db2.Column(db2.Integer, db2.ForeignKey('common_ingredients.id'), primary_key=True, nullable=False)
    user_id = db2.Column(db2.Integer, db2.ForeignKey('users.id'), primary_key=True, nullable=False)
    stock = db2.Column(db2.Integer)

class CommonCocktail(db2.Model):
    __tablename__ = 'common_cocktails'

    id = db2.Column(db2.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db2.Column(db2.String(50), nullable=False)
    build = db2.Column(db2.String(1000))
    source = db2.Column(db2.String(50))
    family = db2.Column(db2.String(50))

    ingredients = db2.relationship('CommonIngredient', secondary='common_amounts')


@app.after_request
# No database operations
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET", "POST"])
# Migration Finished
@login_required
def index():
    if request.method == "GET":
        return render_template(
            "index.html", defaults=session["defaults"]
        )
    elif request.method == "POST":
        cocktails = request.form.get('cocktailswitch')
        if cocktails:
            # Update database defaults for next login
            cocktailupdate = text("UPDATE users SET default_cocktails = 'on' WHERE id = :user_id")
            db2.session.execute(cocktailupdate, {"user_id": session["user_id"]})
            db2.session.commit()

            # db.execute("UPDATE users SET default_cocktails = ? WHERE id = ?", 'on', session["user_id"])

            # Update current session defaults
            session["defaults"] = 'on'
        else:
            # Update database defaults for next login
            cocktailupdate = text("UPDATE users SET default_cocktails = '' WHERE id = :user_id")
            db2.session.execute(cocktailupdate, {"user_id": session["user_id"]})
            db2.session.commit()
            # db.execute("UPDATE users SET default_cocktails = ? WHERE id = ?", '', session["user_id"])

            # Update current session defaults
            session["defaults"] = ''
        print(f"{cocktails}")
        return render_template("index.html")

@app.route("/whatstodrink")
# No Database Operations
@login_required
def whatstodrink():

    return render_template(
        "whatstodrink.html", defaults=session["defaults"]
    )

@app.route("/missingone")
# No Database Operations
@login_required
def missingone():

   
    return render_template(
        "missingone.html", defaults=session["defaults"]
    )

@app.route("/missingoneall")
# Migration Finished
@login_required
def missingoneall():

    cocktailsquery = text("SELECT cc.id, cc.name, cc.family, cc.build, cc.source "
        "FROM common_cocktails cc "
        "JOIN common_amounts ca ON cc.id = ca.cocktail_id "
        "LEFT JOIN common_ingredients ci ON ca.ingredient_id = ci.id "
        "LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id "
        "WHERE (cs.stock != 'on' AND cs.user_id = :user_id) "
        "GROUP BY cc.id "
        "HAVING COUNT(*) = 1 "
        "UNION "
        "SELECT c.id, c.name, c.family, c.build, c.source "
        "FROM cocktails c "
        "JOIN amounts a ON c.id = a.cocktail_id "
        "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
        "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
        "WHERE (a.ingredient_source = 'user' AND i.stock != 'on' AND i.user_id = :user_id) "
        "OR (a.ingredient_source = 'common' AND cs.stock != 'on' AND cs.user_id = :user_id) "
        "GROUP BY c.id "
        "HAVING COUNT(*) = 1") 
    cocktails = db2.session.execute(cocktailsquery, {"user_id": session["user_id"]}).fetchall()
    # cocktails = db.execute(
    #     "SELECT cc.id, cc.name, cc.family, cc.build, cc.source "
    #     "FROM common_cocktails cc "
    #     "JOIN common_amounts ca ON cc.id = ca.cocktail_id "
    #     "LEFT JOIN common_ingredients ci ON ca.ingredient_id = ci.id "
    #     "LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id "
    #     "WHERE (cs.stock != 'on' AND cs.user_id = ?) "
    #     "GROUP BY cc.id "
    #     "HAVING COUNT(*) = 1 "
    #     "UNION "
    #     "SELECT c.id, c.name, c.family, c.build, c.source "
    #     "FROM cocktails c "
    #     "JOIN amounts a ON c.id = a.cocktail_id "
    #     "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
    #     "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
    #     "WHERE (a.ingredient_source = 'user' AND i.stock != 'on' AND i.user_id = ?) "
    #     "OR (a.ingredient_source = 'common' AND cs.stock != 'on' AND cs.user_id = ?) "
    #     "GROUP BY c.id "
    #     "HAVING COUNT(*) = 1", session["user_id"], session["user_id"], session["user_id"]
    # )

    missingquery = text("WITH sad_cocktails AS (\
            SELECT cc.id "
            "FROM common_cocktails cc "
            "JOIN common_amounts ca ON cc.id = ca.cocktail_id "
            "LEFT JOIN common_ingredients ci ON ca.ingredient_id = ci.id "
            "LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id "
            "WHERE (cs.stock != 'on' AND cs.user_id = :user_id) "
            "GROUP BY cc.id "
            "HAVING COUNT(*) = 1 "
            "UNION "
            "SELECT c.id "
            "FROM cocktails c "
            "JOIN amounts a ON c.id = a.cocktail_id "
            "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
            "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
            "WHERE (a.ingredient_source = 'user' AND i.stock != 'on' AND i.user_id = :user_id AND c.user_id = :user_id) "
            "OR (a.ingredient_source = 'common' AND cs.stock != 'on' AND cs.user_id = :user_id AND c.user_id = :user_id) "
            "GROUP BY c.id "
            "HAVING COUNT(*) = 1 \
        ), \
        sad_amounts AS (\
            SELECT ingredient_id FROM amounts WHERE (cocktail_id IN sad_cocktails AND user_id = :user_id)\
            UNION\
            SELECT ingredient_id FROM common_amounts WHERE cocktail_id IN sad_cocktails\
        )\
        SELECT id, name FROM ingredients WHERE (id IN sad_amounts AND stock != 'on') \
        UNION \
        SELECT ci.id, ci.name FROM common_ingredients ci \
        JOIN common_stock cs ON ci.id = cs.ingredient_id \
        WHERE (cs.stock != 'on' AND cs.user_id = :user_id AND ci.id IN sad_amounts) \
        GROUP BY ci.id")
    missing_ingredients = db2.session.execute(missingquery, {"user_id": session["user_id"]}).fetchall()
    # missing_ingredients = db.execute(
    #     "WITH sad_cocktails AS (\
    #         SELECT cc.id "
    #         "FROM common_cocktails cc "
    #         "JOIN common_amounts ca ON cc.id = ca.cocktail_id "
    #         "LEFT JOIN common_ingredients ci ON ca.ingredient_id = ci.id "
    #         "LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id "
    #         "WHERE (cs.stock != 'on' AND cs.user_id = ?) "
    #         "GROUP BY cc.id "
    #         "HAVING COUNT(*) = 1 "
    #         "UNION "
    #         "SELECT c.id "
    #         "FROM cocktails c "
    #         "JOIN amounts a ON c.id = a.cocktail_id "
    #         "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
    #         "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
    #         "WHERE (a.ingredient_source = 'user' AND i.stock != 'on' AND i.user_id = ? AND c.user_id = ?) "
    #         "OR (a.ingredient_source = 'common' AND cs.stock != 'on' AND cs.user_id = ? AND c.user_id = ?) "
    #         "GROUP BY c.id "
    #         "HAVING COUNT(*) = 1 \
    #     ), \
    #     sad_amounts AS (\
    #         SELECT ingredient_id FROM amounts WHERE (cocktail_id IN sad_cocktails AND user_id = ?)\
    #         UNION\
    #         SELECT ingredient_id FROM common_amounts WHERE cocktail_id IN sad_cocktails\
    #     )\
    #     SELECT id, name FROM ingredients WHERE (id IN sad_amounts AND stock != 'on') \
    #     UNION \
    #     SELECT ci.id, ci.name FROM common_ingredients ci \
    #     JOIN common_stock cs ON ci.id = cs.ingredient_id \
    #     WHERE (cs.stock != 'on' AND cs.user_id = ? AND ci.id IN sad_amounts) \
    #     GROUP BY ci.id"\
    #     , session["user_id"], session["user_id"], session["user_id"], session["user_id"], session["user_id"], session["user_id"], session["user_id"]
    # )
    ingredientsquery = text("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = :user_id")
    ingredients = db2.session.execute(ingredientsquery, {"user_id": session["user_id"]}).fetchall()
   
    amountsquery = text("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = :user_id")
    amounts = db2.session.execute(amountsquery, {"user_id": session["user_id"]}).fetchall()
    # ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
    # amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = ?", session["user_id"])

    return render_template(
        "missingoneall.html", cocktails=cocktails, ingredients=ingredients, amounts=amounts, missing_ingredients=missing_ingredients, defaults=session["defaults"]
    )

@app.route("/missingoneuser")
# Migration Complete
@login_required
def missingoneuser():

    cocktailquery = text("SELECT c.name, c.id, c.family, c.build, c.source "
        "FROM cocktails c "
        "JOIN amounts a ON c.id = a.cocktail_id "
        "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
        "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
        "WHERE (\
            (a.ingredient_source = 'user' AND i.stock != 'on' AND i.user_id = :user_id AND c.user_id = :user_id) "
            "OR \
            (a.ingredient_source = 'common' AND cs.stock != 'on' AND cs.user_id = :user_id AND c.user_id = :user_id) "
            ") \
        GROUP BY c.id "
        "HAVING COUNT(*) = 1")
    cocktails = db2.session.execute(cocktailquery, {"user_id": session["user_id"]}).fetchall()
    # cocktails = db.execute(
    #     "SELECT c.name, c.id, c.family, c.build, c.source "
    #     "FROM cocktails c "
    #     "JOIN amounts a ON c.id = a.cocktail_id "
    #     "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
    #     "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
    #     "WHERE (\
    #         (a.ingredient_source = 'user' AND i.stock != 'on' AND i.user_id = ? AND c.user_id = ?) "
    #         "OR \
    #         (a.ingredient_source = 'common' AND cs.stock != 'on' AND cs.user_id = ? AND c.user_id = ?) "
    #         ") \
    #     GROUP BY c.id "
    #     "HAVING COUNT(*) = 1", session["user_id"], session["user_id"], session["user_id"], session["user_id"]
    # )
    print(f'cocktails missing 1: {cocktails}')

    missingquery = text("WITH sad_cocktails AS (\
            SELECT c.id "
            "FROM cocktails c "
            "JOIN amounts a ON c.id = a.cocktail_id "
            "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
            "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
            "WHERE (\
                (a.ingredient_source = 'user' AND i.stock != 'on' AND i.user_id = :user_id AND c.user_id = :user_id) "
                "OR \
                (a.ingredient_source = 'common' AND cs.stock != 'on' AND cs.user_id = :user_id AND c.user_id = :user_id) "
                ") \
            GROUP BY c.id "
            "HAVING COUNT(*) = 1\
        ),\
        sad_amounts AS (\
            SELECT ingredient_id FROM amounts WHERE (cocktail_id IN sad_cocktails AND user_id = :user_id)\
            UNION\
            SELECT ingredient_id FROM common_amounts WHERE cocktail_id IN sad_cocktails\
        )\
        SELECT id, name FROM ingredients WHERE (id IN sad_amounts AND stock != 'on') \
        UNION \
        SELECT ci.id, ci.name FROM common_ingredients ci \
        JOIN common_stock cs ON ci.id = cs.ingredient_id \
        WHERE (cs.stock != 'on' AND cs.user_id = :user_id AND ci.id IN sad_amounts) \
        GROUP BY ci.id")
    missing_ingredients = db2.session.execute(missingquery, {"user_id": session["user_id"]}).fetchall()
    # missing_ingredients = db.execute(
    #     "WITH sad_cocktails AS (\
    #         SELECT c.id "
    #         "FROM cocktails c "
    #         "JOIN amounts a ON c.id = a.cocktail_id "
    #         "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
    #         "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
    #         "WHERE (\
    #             (a.ingredient_source = 'user' AND i.stock != 'on' AND i.user_id = ? AND c.user_id = ?) "
    #             "OR \
    #             (a.ingredient_source = 'common' AND cs.stock != 'on' AND cs.user_id = ? AND c.user_id = ?) "
    #             ") \
    #         GROUP BY c.id "
    #         "HAVING COUNT(*) = 1\
    #     ),\
    #     sad_amounts AS (\
    #         SELECT ingredient_id FROM amounts WHERE (cocktail_id IN sad_cocktails AND user_id = ?)\
    #         UNION\
    #         SELECT ingredient_id FROM common_amounts WHERE cocktail_id IN sad_cocktails\
    #     )\
    #     SELECT id, name FROM ingredients WHERE (id IN sad_amounts AND stock != 'on') \
    #     UNION \
    #     SELECT ci.id, ci.name FROM common_ingredients ci \
    #     JOIN common_stock cs ON ci.id = cs.ingredient_id \
    #     WHERE (cs.stock != 'on' AND cs.user_id = ? AND ci.id IN sad_amounts) \
    #     GROUP BY ci.id"\
    #     , session["user_id"], session["user_id"], session["user_id"], session["user_id"], session["user_id"], session["user_id"] 
    # )
    ingredientsquery = text("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = :user_id")
    ingredients = db2.session.execute(ingredientsquery, {"user_id": session["user_id"]}).fetchall()
   
    amountsquery = text("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = :user_id")
    amounts = db2.session.execute(amountsquery, {"user_id": session["user_id"]}).fetchall()

    # ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
    # amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = ?", session["user_id"])
    print(f'missing ingredients:{missing_ingredients}')
    return render_template(
        "missingoneuser.html", cocktails=cocktails, ingredients=ingredients, amounts=amounts, missing_ingredients=missing_ingredients
    )
  
@app.route("/whatstodrinkuser")
# Migration Complete
@login_required
def whatstodrinkuser():

    cocktailsquery = text("SELECT c.name, c.id, c.family, c.build, c.source "
        "FROM cocktails c "
        "JOIN amounts a ON c.id = a.cocktail_id "
        "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
        "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
        "WHERE (a.ingredient_source = 'user' AND i.stock = 'on' AND i.user_id = :user_id AND c.user_id = :user_id) "
        "OR (a.ingredient_source = 'common' AND cs.stock = 'on' AND cs.user_id = :user_id AND c.user_id = :user_id) "
        "GROUP BY c.id "
        "HAVING COUNT(*) = (SELECT COUNT(*) FROM amounts a3 WHERE a3.cocktail_id = c.id)")
    cocktails = db2.session.execute(cocktailsquery, {"user_id": session["user_id"]}).fetchall()
    # cocktails = db.execute(
    #     "SELECT c.name, c.id, c.family, c.build, c.source "
    #     "FROM cocktails c "
    #     "JOIN amounts a ON c.id = a.cocktail_id "
    #     "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
    #     "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
    #     "WHERE (a.ingredient_source = 'user' AND i.stock = 'on' AND i.user_id = ? AND c.user_id = ?) "
    #     "OR (a.ingredient_source = 'common' AND cs.stock = 'on' AND cs.user_id = ? AND c.user_id = ?) "
    #     "GROUP BY c.id "
    #     "HAVING COUNT(*) = (SELECT COUNT(*) FROM amounts a3 WHERE a3.cocktail_id = c.id)", session["user_id"], session["user_id"], session["user_id"], session["user_id"]
    # )

    ingredientsquery = text("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = :user_id")
    ingredients = db2.session.execute(ingredientsquery, {"user_id": session["user_id"]}).fetchall()
   
    amountsquery = text("SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = :user_id")
    amounts = db2.session.execute(amountsquery, {"user_id": session["user_id"]}).fetchall()
    # ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
    # amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = ?", session["user_id"])
    families = set(Cocktail.family for Cocktail in cocktails)

    return render_template(
        "whatstodrinkuser.html", cocktails=cocktails, ingredients=ingredients, amounts=amounts, families=families
    )

@app.route("/login", methods=["GET", "POST"])
# Migration Finished
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        uname = request.form.get("username")
        password = request.form.get("password")
        stmt = select(User).where(User.username == uname)
        rows = db2.session.scalars(stmt).first()
        # rows = db2.session.scalar(db2.select(User).where(User.username == uname))

        # rows = db.execute(
        #     "SELECT * FROM users WHERE username = ?", request.form.get("username")
        # )

        # Ensure username exists and password is correct
        if not rows or not check_password_hash(
            rows.hash, password
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows.id
        # Check default cocktail setting
        session["defaults"] = rows.default_cocktails

        # make sure user has stock values for all common ingredients on login
        query = select(CommonIngredient.id)
        common_ingredients = db2.session.scalars(query).all()
        # common_ingredients = db.execute("SELECT id FROM common_ingredients")
        # get all ids in common_ingredients
        for ingredient in common_ingredients:
            # check if user has ingredient in common_stock
            result = db2.session.scalars(select(CommonStock.ingredient_id).where(CommonStock.user_id == session["user_id"]).where(CommonStock.ingredient_id == ingredient)).first()
            # result = db.execute("SELECT ingredient_id FROM common_stock WHERE user_id = ? AND ingredient_id = ?", session["user_id"],  ingredient)

            # if not, insert a default
            if not result:
                newingredient = CommonStock(ingredient_id=ingredient, user_id = session["user_id"], stock='')
                db2.session.add(newingredient)
                db2.session.commit()
                # db.execute("INSERT INTO common_stock (user_id, ingredient_id, stock) VALUES (?, ?, ?)", session["user_id"], ingredient_id, '')


        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
# No Database Operations
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
# Migration Finished
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # check that passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password and confirmation must match", 400)

        # check to see if user exists
        uname = request.form.get("username")
        rows = db2.session.scalars(select(User.username).where(User.username == uname)).first()
        # rows = db.execute("SELECT username FROM users WHERE username = ?", uname)
        if not rows:
            # insert into users table
            hash = generate_password_hash(
                request.form.get("password"), method="pbkdf2", salt_length=16
            )
            newuser = User(username=uname, hash=hash, default_cocktails='on')
            db2.session.add(newuser)
            db2.session.commit()
            # db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", uname, hash)
            # assign default ingredients to stock

        else:
            return apology("username already exists", 400)
        return redirect("/")
    # if GET
    else:
        return render_template("register.html")


@app.route("/addingredient", methods=["GET", "POST"])
# Migration Complete
@login_required
def addingredient():

    # reached via post
     if request.method == "POST":
        # Ensure ingredient was submitted
        if not request.form.get("ingredientname"):
            return apology("must add ingredient", 400)

        # Ensure type was submitted
        elif not request.form.get("type"):
            return apology("must select ingredient type", 400)

        # Query database for ingredient
        name = request.form.get("ingredientname")
        query = text("SELECT name FROM ingredients WHERE name = :name AND user_id = :user_id UNION SELECT name FROM common_ingredients WHERE name = :name")
        rows = db2.session.execute(query, {"name": name, "user_id": session["user_id"]}).fetchall()
        # rows = db.execute(
        #     "SELECT name FROM ingredients WHERE name = ? AND user_id = ? UNION SELECT name FROM common_ingredients WHERE name = ?", request.form.get("ingredientname"), session["user_id"], request.form.get("ingredientname")
        # )

        # Ensure username exists and password is correct
        if rows:
            return apology("ingredient already exists", 400)
        else:
            # insert new ingredient into db
            name = request.form.get("ingredientname")
            type = request.form.get("type")
            stock = request.form.get("stock")
            short_name = request.form.get("short_name")
            notes = request.form.get("notes")

            insert = text("INSERT INTO ingredients (user_id, name, type, stock, short_name, notes) VALUES(:user_id, :name, :type, :stock, :short_name, :notes)")

            db2.session.execute(insert, {"user_id": session["user_id"], "name": name, "type": type, "stock": stock, "short_name": short_name, "notes": notes})
            db2.session.commit()
            # db.execute(
            #     "INSERT INTO ingredients (user_id, name, type, stock, short_name, notes) VALUES(?, ?, ?, ?, ?, ?)",
            #     session["user_id"],
            #     request.form.get("ingredientname"),
            #     request.form.get("type"),
            #     request.form.get("stock"),
            #     request.form.get("short-name"),
            #     request.form.get("notes")
            # )
            flash('Success! Ingredient Added')
        return render_template(
            "addingredient.html"
        )
    # User reached route via GET (as by clicking a link or via redirect)
     else:
        return render_template(
            "addingredient.html"
        )

@app.route("/ingredientmodal", methods=["GET", "POST"])
# Migration Finished
@login_required
def ingredientmodal():

    # reached via post
    if request.method == "POST":
        # Ensure ingredient was submitted
        if not request.form.get("ingredientname"):
            return apology("must add ingredient", 400)

        # Ensure type was submitted
        elif not request.form.get("type"):
            return apology("must select ingredient type", 400)

        # Query database for ingredient

        rowsquery = text("SELECT name FROM ingredients WHERE name = :name AND user_id = :user_id UNION SELECT name FROM common_ingredients WHERE name = :name")
        rows = db2.session.execute(rowsquery, {"name": request.form.get("ingredientname"), "user_id": session["user_id"]}).fetchall()
        # rows = db.execute(
        #     "SELECT name FROM ingredients WHERE name = ? AND user_id = ? UNION SELECT name FROM common_ingredients WHERE name = ?", request.form.get("ingredientname"), session["user_id"], request.form.get("ingredientname")
        # )

        # Ensure username exists and password is correct
        if rows:
            return apology("ingredient already exists", 400)
        else:
            # insert new ingredient into db
            insertquery = text("INSERT INTO ingredients (user_id, name, type, stock, short_name, notes) VALUES(:user_id, :name, :type, :stock, :short_name, :notes)")
            db2.session.execute(insertquery, {"user_id": session["user_id"], "name": request.form.get("ingredientname"), "type": request.form.get("type"), "stock": request.form.get("stock"), "short_name": request.form.get("short-name"), "notes": request.form.get("notes)")})
            db2.session.commit()
            # db.execute(
            #     "INSERT INTO ingredients (user_id, name, type, stock, short_name, notes) VALUES(?, ?, ?, ?, ?, ?)",
            #     session["user_id"],
            #     request.form.get("ingredientname"),
            #     request.form.get("type"),
            #     request.form.get("stock"),
            #     request.form.get("short-name"),
            #     request.form.get("notes")
            # )
        
            # flash('Success! Ingredient Added')
            return "200"
        
      # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template(
            "addingredient.html"
        )

@app.route("/addingredientmodal2", methods=["GET", "POST"])
#Migration Complete
@login_required
def ingredientmodal2():

    # reached via post
     if request.method == "POST":
        # Ensure ingredient was submitted
        if not request.form.get("ingredientname"):
            return apology("must add ingredient", 400)

        # Ensure type was submitted
        elif not request.form.get("type"):
            return apology("must select ingredient type", 400)

        # Query database for ingredient
        rowsquery = text("SELECT name FROM ingredients WHERE name = :ingredientname AND user_id = :user_id UNION SELECT name FROM common_ingredients WHERE name = :ingredientname")
        rows = db2.session.execute(rowsquery, {"ingredientname": request.form.get("ingredientname"), "user_id": session["user_id"]}).fetchall()

        # Ensure username exists and password is correct
        if rows:
            return apology("ingredient already exists", 400)
        else:
            # insert new ingredient into db
            new_ingredient = Ingredient(
                user_id=session["user_id"],
                name=request.form.get("ingredientname"),
                type=request.form.get("type"),
                stock=request.form.get("stock"),
                short_name=request.form.get("short-name"),
                notes=request.form.get("notes"),
            )
            db2.session.add(new_ingredient)
            db2.session.commit()    
            
        # flash("Success! Ingredient Added")

        return redirect(url_for("manageingredients", _reload=int(time.time())))
        
      # User reached route via GET (as by clicking a link or via redirect)
     
     else:
        return render_template(
            "addingredientmodal2.html"
        )

@app.route("/manageingredients", methods=["GET", "POST"])
# Migration finished
@login_required
def manageingredients():
    
    if request.method =="GET":

        # check for search queries 
        q = request.args.get('q')

        # if filter bar is used
        
        if q is not None:
            common_query = (
                select(CommonIngredient.type.distinct())
                .select_from(CommonIngredient)
                .outerjoin(CommonStock, (CommonIngredient.id == CommonStock.ingredient_id) & (CommonStock.user_id == session["user_id"]))
                .where(CommonIngredient.name.like('%' + q + '%'))
            )
            user_query = (
                select(Ingredient.type.distinct())
                .select_from(Ingredient)
                .where((Ingredient.user_id == session["user_id"]) & (Ingredient.name.like('%' + q + '%')))
                )
            query = union(common_query, user_query)

            types = db2.session.scalars(query).all()
           

            # types = db.execute("SELECT DISTINCT type FROM (SELECT 'common' AS source, ci.id AS ingredient_id, ci.name, ci.type, ci.short_name, cs.stock \
            #                         FROM common_ingredients ci \
            #                         LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id AND cs.user_id = ? \
            #                         WHERE ci.name LIKE ?\
            #                         UNION SELECT 'user' AS source, i.id AS ingredient_id, i.name, i.type, i.short_name, i.stock \
            #                         FROM ingredients i \
            #                         WHERE i.user_id = ? AND i.name LIKE ?)", session["user_id"], '%'+q+'%', session["user_id"], '%'+q+'%')
            

            # common_query = (
            #     select([literal_column('common').label('source'), CommonIngredient.id, CommonIngredient.name, CommonIngredient.type])
            #     .select_from(CommonIngredient
        #         .outerjoin(CommonStock, (CommonIngredient.id == CommonStock.ingredient_id) & (CommonStock.user_id == session["user_id"]))
        #         .where(CommonIngredient.name.like('%' + q + '%'))
            #     )
            # )
            # user_query = (
            #     select([literal_column('user').label('source'), Ingredient.id, Ingredient.name, Ingredient.type])
            #     .where((Ingredient.user_id == session["user_id"]) & (Ingredient.name.like('%' + q + '%')))
            #     )
            # query = union(common_query, user_query)
            ingredientsquery = text("SELECT 'common' AS source, ci.id AS ingredient_id, ci.name, ci.type, ci.short_name, cs.stock, ci.notes \
                                    FROM common_ingredients ci \
                                    LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id AND cs.user_id = :user_id \
                                    WHERE ci.name LIKE :q\
                                    UNION SELECT 'user' AS source, i.id AS ingredient_id, i.name, i.type, i.short_name, i.stock, i.notes \
                                    FROM ingredients i \
                                    WHERE i.user_id = :user_id AND i.name LIKE :q\
                                    ORDER BY name ASC")
            ingredients = db2.session.execute(ingredientsquery, {"user_id": session["user_id"], "q": '%'+q+'%'}).fetchall()
            
            # ingredients = db.execute("SELECT 'common' AS source, ci.id AS ingredient_id, ci.name, ci.type, ci.short_name, cs.stock, ci.notes \
            #                         FROM common_ingredients ci \
            #                         LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id AND cs.user_id = ? \
            #                         WHERE ci.name LIKE ?\
            #                         UNION SELECT 'user' AS source, i.id AS ingredient_id, i.name, i.type, i.short_name, i.stock, i.notes \
            #                         FROM ingredients i \
            #                         WHERE i.user_id = ? AND i.name LIKE ?\
            #                         ORDER BY name ASC", session["user_id"], '%'+q+'%', session["user_id"], '%'+q+'%'
            #                         )
            

            if request.headers.get('HX-Trigger') == 'search':
                return render_template("/ingredientstable.html", ingredients=ingredients, types=types)
            else:
                return render_template("/manageingredients.html", ingredients=ingredients, types=types)
            
        
        else:
            typesquery = text("SELECT DISTINCT type FROM common_ingredients")
            types = db2.session.execute(typesquery).fetchall()
            ingredientsquery = text("SELECT 'common' AS source, ci.id AS ingredient_id, ci.name, ci.type, ci.short_name, cs.stock, ci.notes \
                                     FROM common_ingredients ci \
                                     LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id AND cs.user_id = :user_id \
                                     UNION SELECT 'user' AS source, i.id AS ingredient_id, i.name, i.type, i.short_name, i.stock, i.notes \
                                     FROM ingredients i \
                                     WHERE i.user_id = :user_id \
                                     ORDER BY name ASC")
            ingredients = db2.session.execute(ingredientsquery, {"user_id": session["user_id"]}).fetchall()
            return render_template(
                "manageingredients.html", ingredients=ingredients, types=types
            )
    elif request.method =="POST":
        for key, value, in request.form.items():
            if key.startswith('stock_'):
                ingredient_name = key.replace('stock_', '')
                ingredient_id = request.form.get(f'id_{ingredient_name}')
                ingredient_source = request.form.get(f'src_{ingredient_name}')
                ingredient_stock = value
            elif key.startswith('id_'):
                ingredient_name = key.replace('id_', '')
                ingredient_id = value
                ingredient_source = request.form.get(f'src_{ingredient_name}')
                ingredient_stock = request.form.get(f'stock_{ingredient_name}')

                # set stock for user ingredients
                # Determine the correct table and column for the update
                table_name = "common_stock" if ingredient_source == "common" else "ingredients"
                id_column = "ingredient_id" if ingredient_source == "common" else "id"
                stock = 'on' if ingredient_stock == 'on' else ''

                print(f"{table_name}")
                print(f"{id_column}")
                print(f"{stock}")
                print(f"{ingredient_id}")
                try:
                    with db2.session.begin():
                        sql_query = text(f"UPDATE {table_name} SET stock = :stock WHERE {id_column} = :ingredient_id AND user_id = :user_id")
                    
                        # Update the stock value
                        db2.session.execute(sql_query, {"stock": stock, "ingredient_id": ingredient_id, "user_id": session["user_id"]})

                    db2.session.commit()
                except Exception as e:
                    db2.session.rollback()
                    print(f"An error occured: {e}")

                
        return redirect(url_for(
            "manageingredients"
        ))



@app.route("/addcocktail", methods=["GET", "POST"])
# Migration finished
@login_required
def addcocktail():

    if request.method=="GET":
        # query not needed with no select menu for add ingredient
        # ingredientsquery = text("SELECT name, type FROM common_ingredients UNION SELECT name, type FROM ingredients WHERE user_id = :user_id ORDER BY name ASC")
        # ingredients = db2.session.execute(ingredientsquery, {"user_id": session["user_id"]})
        # ingredients = db.execute("SELECT name, type FROM common_ingredients UNION SELECT name, type FROM ingredients WHERE user_id = ? ORDER BY name ASC", session["user_id"])
        # typesquery = text("SELECT type, COUNT(*) as type_count FROM (SELECT type FROM common_ingredients UNION SELECT DISTINCT type FROM ingredients) GROUP BY type ORDER BY type_count DESC")
        # types = db2.session.execute(typesquery).fetchall()
        # types = db.execute("SELECT type, COUNT(*) as type_count FROM (SELECT type FROM common_ingredients UNION SELECT DISTINCT type FROM ingredients) GROUP BY type ORDER BY type_count DESC")
        return render_template(
            "addcocktail.html"
        )
    
    else:
        name = request.form.get('name')
        build = request.form.get('build')
        source = request.form.get('source')
        family = request.form.get('family')
        rawingredients = request.form.getlist('q')
        ingredients = list(filter(None, rawingredients))

        if not name:
            return apology("every good cocktail has a name")
        if not ingredients:
            return apology("an empty glass is not a cocktail")
        rowsquery = text("SELECT name FROM cocktails WHERE name = :name AND user_id = :user_id")
        rows = db2.session.execute(rowsquery, {"name": name, "user_id": session["user_id"]}).fetchall()
        # rows = db.execute(
        #     "SELECT name FROM cocktails WHERE name = ? AND user_id = ?", name, session["user_id"]
        # )
        if rows:
            return apology("You already have a cocktail by that name", 400)


        return render_template(
            "amountsmodal.html", ingredients=ingredients, build=build, source=source, family=family, name=name
        )
    
@app.route("/amounts", methods=["GET", "POST"])
# Migration Finished
@login_required
def amounts():
    # reached via post
    if request.method == "POST":
        build = request.form.get('build')
        source = request.form.get('source')
        family = request.form.get('family')
        name = request.form.get('name')

         # add cocktail to db
        addquery = text("INSERT INTO cocktails (name, build, source, family, user_id) VALUES(:name, :build, :source, :family, :user_id)")
        db2.session.execute(addquery, {"name": name, "build": build, "source": source, "family": family, "user_id": session["user_id"]})
        db2.session.commit()
        # db.execute(
        # "INSERT INTO cocktails (name, build, source, family, user_id) VALUES(?, ?, ?, ?, ?)",
        # name,
        # build,
        # source,
        # family,
        # session["user_id"]
        # )

        for key, value, in request.form.items():
            if key.startswith('amount_'):
                ingredient_name = key.replace('amount_', '')
                sourcequery = text("SELECT 'common' AS source, id FROM common_ingredients \
                    WHERE name = :name \
                    UNION SELECT \
                    'user' AS source, id \
                    FROM ingredients \
                    WHERE name = :name AND user_id = :user_id")
                id_source = db2.session.execute(sourcequery, {"name": ingredient_name, "user_id": session["user_id"]}).fetchone()
                # ingredient_source = db.execute(\
                #     "SELECT 'common' AS source, id FROM common_ingredients \
                #     WHERE name = ? \
                #     UNION SELECT \
                #     'user' AS source, id \
                #     FROM ingredients \
                #     WHERE name = ? AND user_id = ?"\
                #     , ingredient_name, ingredient_name, session["user_id"])[0]['source']
                amount = value
                # idquery = text("SELECT 'common' AS source, id FROM common_ingredients WHERE name = :name UNION SELECT 'user' AS source, id FROM ingredients WHERE name = :name AND user_id = :user_id")
                # ingredient_id = db2.session.execute(idquery, {"name": ingredient_name, "user_id": session["user_id"]}).fetchone()
                # ingredient_id = (db.execute("SELECT 'common' AS source, id FROM common_ingredients WHERE name = ? UNION SELECT 'user' AS source, id FROM ingredients WHERE name = ? AND user_id = ?", ingredient_name, ingredient_name, session["user_id"]))[0]['id']
                
                # get cocktail id
                c_id_query = text("SELECT id FROM cocktails WHERE name = :name AND user_id = :user_id")
                cocktail_id = db2.session.scalar(c_id_query, {"name": name, "user_id": session["user_id"]})
                # cocktailidquery = text("SELECT id from cocktails WHERE name = :name AND user_id = ?")
                # cocktail_id = db.execute("SELECT id from cocktails WHERE name = ? AND user_id = ?", name, session["user_id"])[0]['id']
                #add ingredients and amounts to db
                insertquery = text("INSERT INTO amounts (cocktail_id, ingredient_id, amount, ingredient_source, user_id) VALUES(:cocktail_id, :ingredient_id, :amount, :ingredient_source, :user_id)")
                db2.session.execute(insertquery, {"cocktail_id": cocktail_id, "ingredient_id": id_source.id, "amount": amount, "ingredient_source": id_source.source, "user_id": session["user_id"]})
                db2.session.commit()
                # db.execute(
                #     "INSERT INTO amounts (cocktail_id, ingredient_id, amount, ingredient_source, user_id) VALUES(?, ?, ?, ?, ?)",
                #     cocktail_id,
                #     ingredient_id,
                #     amount,
                #     ingredient_source,
                #     session["user_id"])
                flash('Success! Cocktail Added')
                

    
    return redirect(url_for(
        "addcocktail"
    ))

@app.route("/ingredientsearch")
# Migration Complete
def search():
    q = request.args.get("q")

    if q:
        resultsquery = text("SELECT name FROM common_ingredients\
                             WHERE name LIKE :q\
                             UNION\
                             SELECT name FROM ingredients\
                             WHERE name LIKE :q AND user_id = :user_id\
                             LIMIT 10")
        results = db2.session.execute(resultsquery, {"q": '%'+q+'%', "user_id": session["user_id"]}).fetchall()
        # results = db.execute("SELECT name FROM common_ingredients\
                            #  WHERE name LIKE ?\
                            #  UNION\
                            #  SELECT name FROM ingredients\
                            #  WHERE name LIKE ? AND user_id = ?\
                            #  LIMIT 10", '%'+q+'%', '%'+q+'%', session["user_id"])
    else:
        results = []

    return render_template("ingredientsearch.html", results=results)

@app.route("/modify_ingredient", methods=["GET", "POST"])
# Migration Finished
def modify_ingredient():
    ingredient = request.form.get('modifiedIngredientName')
    new_name = request.form.get('renameText')

    
    if request.method == "POST":
        if "renamebutton" in request.form:
        # done
            if new_name:
                checkquery = text("SELECT id FROM ingredients WHERE name = :name AND user_id = :user_id UNION SELECT id FROM common_ingredients WHERE name = :name")
                check = db2.session.execute(checkquery, {"name": new_name, "user_id": session["user_id"]}).fetchall()
                # check = db.execute("SELECT id FROM ingredients WHERE name = ? AND user_id = ? UNION SELECT id FROM common_ingredients WHERE name = ?", new_name, session["user_id"], new_name)
                if check:
                    return apology("an ingredient with that name already exists")
                else:
                    renamequery = text("UPDATE ingredients SET name = :name WHERE name = :old_name AND user_id = :user_id")
                    db2.session.execute(renamequery, {"name": new_name, "old_name": ingredient, "user_id": session["user_id"]})
                    db2.session.commit()
                    # db.execute("UPDATE ingredients SET name = ? WHERE name = ? AND user_id = ?", new_name, ingredient, session["user_id"])
                    # flash("Ingredient Renamed")
                    return redirect(url_for('manageingredients', _reload=int(time.time())))
            else:
                return apology("An ingredient has not name")
            
        elif "submitbutton" in request.form:
        # done
            newtype = request.form.get('type')
            newnotes = request.form.get('notes')
            ingredient = request.form.get('modifiedIngredientName')
            updatequery = text("UPDATE ingredients SET type = :type, notes = :notes WHERE name = :name AND user_id = :user_id")
            db2.session.execute(updatequery,  {"type": newtype, "notes": newnotes, "name": ingredient, "user_id": session["user_id"]})
            db2.session.commit()                  
            # db.execute("UPDATE ingredients SET type = ?, notes = ? WHERE name = ? AND user_id = ?", newtype, newnotes, ingredient, session["user_id"])
            return redirect(url_for('manageingredients', _reload=int(time.time())))


        elif "deletebutton" in request.form:
        # done
            rowsquery = text("SELECT cocktails.name FROM cocktails \
                              JOIN amounts ON cocktails.id = amounts.cocktail_id \
                              LEFT JOIN ingredients ON amounts.ingredient_id = ingredients.id \
                              WHERE ingredients.name = :name \
                              GROUP BY cocktails.name")
            # rows = db.execute("SELECT cocktails.name FROM cocktails \
                            #   JOIN amounts ON cocktails.id = amounts.cocktail_id \
                            #   LEFT JOIN ingredients ON amounts.ingredient_id = ingredients.id \
                            #   WHERE ingredients.name = ? \
                            #   GROUP BY cocktails.name", ingredient)
            rows = db2.session.execute(rowsquery, {"name": ingredient}).fetchall()
            if not rows:
                return render_template(
                    "areyousure.html", ingredient=ingredient
                )
            else:
                return render_template(
                    "cannotdelete.html", rows=rows, ingredient=ingredient
                )
        elif "modifybutton" in request.form:
        # done
            name = request.form.get('name')
            ingredientquery = text("SELECT id, name, type, short_name, notes FROM ingredients WHERE name = :name AND user_id = :user_id")
            ingredient = db2.session.execute(ingredientquery, {"name": name, "user_id": session["user_id"]}).fetchall()
            print(f"{ingredient}")
            # ingredient = db.execute("SELECT id, name, type, short_name, notes FROM ingredients WHERE name = ? AND user_id = ?", name, session["user_id"])
            typesquery = text("SELECT DISTINCT type FROM common_ingredients")
            types = db2.session.execute(typesquery).fetchall()
            if ingredient:
                return render_template("modifyingredient.html", ingredient=ingredient, types=types)
            else:
                return apology("Common Ingredients cannot be modified yet")
        
        elif "deleteconfirmed" in request.form:
        # done
            ingredient_delete = request.form.get("ingredient_delete")
            deletequery = text("DELETE FROM ingredients WHERE name = :name AND user_id = :user_id")
            db2.session.execute(deletequery, {"name": ingredient_delete, "user_id": session["user_id"]})
            db2.session.commit()

            # flash('Ingredient Deleted')
            # db.execute("DELETE FROM ingredients WHERE name = ? AND user_id = ?", ingredient_delete, session["user_id"])
            return redirect(url_for("manageingredients", _reload=int(time.time())))
        
        elif "cancel" in request.form:
            return redirect(url_for("manageingredients", _reload=int(time.time())))
        elif "close" in request.form:
            return redirect(url_for("manageingredients", _reload=int(time.time())))
        
  
@app.route("/viewcocktails", methods=["GET", "POST"])
# No Database Operations
def viewcocktails():

    return render_template(
        "viewcocktails.html", defaults=session["defaults"]
    )

@app.route("/viewallcocktails")
# Migration finished
def viewallcocktails():

    allquery = text("SELECT 'user' AS csource, name, id, family, build, source \
        FROM cocktails \
        WHERE user_id = :user_id \
        UNION \
        SELECT 'common' AS csource, name, id, family, build, source \
        FROM common_cocktails")
    allcocktails = db2.session.execute(allquery, {"user_id": session["user_id"]}).fetchall()
    # allcocktails = db.execute(
    #    "SELECT 'user' AS csource, name, id, family, build, source \
    #     FROM cocktails \
    #     WHERE user_id = ? \
    #     UNION \
    #     SELECT 'common' AS csource, name, id, family, build, source \
    #     FROM common_cocktails", session["user_id"]
    # )
    ingredientsquery = text("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = :user_id")
    ingredients = db2.session.execute(ingredientsquery, {"user_id": session["user_id"]}).fetchall()
    # ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
    amountsquery = text("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = :user_id")
    amounts = db2.session.execute(amountsquery, {"user_id": session["user_id"]}).fetchall()
    # amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = ?", session["user_id"])
    allfamilies = set(Cocktail.family for Cocktail in allcocktails)

    return render_template(
        "viewallcocktails.html", allcocktails=allcocktails, ingredients=ingredients, amounts=amounts, allfamilies=allfamilies, defaults=session["defaults"]
    )

@app.route("/viewcommon")
# Migration Finished
def viewcommon():
    commoncocktailsquery = text(
        "SELECT name, id, family, build, source "
        "FROM common_cocktails "
    )
    commoncocktails = db2.session.execute(commoncocktailsquery).fetchall()

    ingredientsquery = text("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = :user_id")
    ingredients = db2.session.execute(ingredientsquery, {"user_id": session["user_id"]}).fetchall()
    # ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
    amountsquery = text("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = :user_id")
    amounts = db2.session.execute(amountsquery, {"user_id": session["user_id"]}).fetchall()
    # amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = ?", session["user_id"])
    allfamilies = set(Cocktail.family for Cocktail in commoncocktails)
    
    return render_template(
        "viewcommon.html", commoncocktails=commoncocktails, ingredients=ingredients, amounts=amounts, allfamilies=allfamilies
    )
    


@app.route("/viewuser")
# Migration Finished
def viewuser():
    cocktailquery = text("SELECT name, id, family, build, source \
                        FROM cocktails \
                        WHERE user_id = :user_id")
   
    usercocktails = db2.session.execute(cocktailquery, {"user_id": session["user_id"]}).fetchall()
    print(f"{usercocktails}")
    # usercocktails = db.execute(
    #     "SELECT name, id, family, build, source \
    #     FROM cocktails \
    #     WHERE user_id = ?", session["user_id"]
    # )
    ingredientsquery = text("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = :user_id")
    ingredients = db2.session.execute(ingredientsquery, {"user_id": session["user_id"]}).fetchall()
    # ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
        
    amountsquery = text("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = :user_id")
    amounts = db2.session.execute(amountsquery, {"user_id": session["user_id"]}).fetchall()
    # amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = ?", session["user_id"])
    userfamilies = set(Cocktail.family for Cocktail in usercocktails)

    return render_template(
        "viewuser.html", ingredients=ingredients, amounts=amounts, usercocktails=usercocktails, userfamilies=userfamilies
    )


@app.route("/viewingredientmodal")
# No Database Operations
def viewingredientmodal():
    return render_template("viewingredientmodal.html")


@app.route("/modifycocktailmodal")
# No Database Operations
def modifycocktailmodal():
    return render_template("modifycocktailmodal.html")

@app.route("/addingredientmodal")
# No Database Operations
def addingredientmodal():
    return render_template("addingredientmodal.html")

@app.route("/about")
# No Database Operations
def about():
    return render_template("about.html")

@app.route("/whatstodrinkall")
# Migration Finished
def whatstodrinkall():

    cocktailquery = text( "SELECT cc.name, cc.id, cc.family, cc.build, cc.source "
    "FROM common_cocktails cc "
    "JOIN common_amounts ca ON cc.id = ca.cocktail_id "
    "LEFT JOIN common_ingredients ci ON ca.ingredient_id = ci.id "
    "LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id "
    "WHERE (cs.stock = 'on' AND cs.user_id = :user_id) "
    "GROUP BY cc.id "
    "HAVING COUNT(*) = (SELECT COUNT(*) FROM common_amounts a2 WHERE a2.cocktail_id = cc.id) "
    "UNION "
    "SELECT c.name, c.id, c.family, c.build, c.source "
    "FROM cocktails c "
    "JOIN amounts a ON c.id = a.cocktail_id "
    "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
    "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
    "WHERE (a.ingredient_source = 'user' AND i.stock = 'on' AND i.user_id = :user_id AND c.user_id = :user_id) "
    "OR (a.ingredient_source = 'common' AND cs.stock = 'on' AND cs.user_id = :user_id AND c.user_id = :user_id) "
    "GROUP BY c.id "
    "HAVING COUNT(*) = (SELECT COUNT(*) FROM amounts a3 WHERE a3.cocktail_id = c.id)")
    cocktails = db2.session.execute(cocktailquery, {"user_id": session["user_id"]}).fetchall()
    # cocktails = db.execute(
    # "SELECT cc.name, cc.id, cc.family, cc.build, cc.source "
    # "FROM common_cocktails cc "
    # "JOIN common_amounts ca ON cc.id = ca.cocktail_id "
    # "LEFT JOIN common_ingredients ci ON ca.ingredient_id = ci.id "
    # "LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id "
    # "WHERE (cs.stock = 'on' AND cs.user_id = ?) "
    # "GROUP BY cc.id "
    # "HAVING COUNT(*) = (SELECT COUNT(*) FROM common_amounts a2 WHERE a2.cocktail_id = cc.id) "
    # "UNION "
    # "SELECT c.name, c.id, c.family, c.build, c.source "
    # "FROM cocktails c "
    # "JOIN amounts a ON c.id = a.cocktail_id "
    # "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
    # "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
    # "WHERE (a.ingredient_source = 'user' AND i.stock = 'on' AND i.user_id = ? AND c.user_id = ?) "
    # "OR (a.ingredient_source = 'common' AND cs.stock = 'on' AND cs.user_id = ? AND c.user_id = ?) "
    # "GROUP BY c.id "
    # "HAVING COUNT(*) = (SELECT COUNT(*) FROM amounts a3 WHERE a3.cocktail_id = c.id)", session["user_id"], session["user_id"], session["user_id"], session["user_id"], session["user_id"]
    # )
    ingredientsquery = text("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = :user_id")
    ingredients = db2.session.execute(ingredientsquery, {"user_id": session["user_id"]}).fetchall()
    # ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
        
    amountsquery = text("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = :user_id")
    amounts = db2.session.execute(amountsquery, {"user_id": session["user_id"]}).fetchall()

    # ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
    # amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = ?", session["user_id"])
    families = set(Cocktail.family for Cocktail in cocktails)

    return render_template(
        "whatstodrinkall.html", cocktails=cocktails, ingredients=ingredients, amounts=amounts, families=families
        )

@app.route("/modify_cocktail", methods=["GET", "POST"])
# Migration Complete
def modify_cocktail():
    cocktail = request.form.get('modifiedCocktailName')
    new_name = request.form.get('renameText')

    
    if request.method == "POST":
        if "renamebutton" in request.form:
            # Done
            if new_name:
                rowsquery = text("SELECT name FROM cocktails WHERE name = :new_name AND user_id = :user_id")
                rows = db2.session.execute(rowsquery, {"new_name": new_name, "user_id": session["user_id"]}).fetchall()
                
                if rows:
                    return apology("You already have a cocktail by that name", 400)
                else:
                    update = text("UPDATE cocktails SET name = :new_name WHERE name = :cocktail AND user_id = :user_id")
                    db2.session.execute(update, {"new_name": new_name, "cocktail": cocktail, "user_id": session["user_id"]})
                    db2.session.commit()
                    return redirect(url_for('viewcocktails'))
            else:
                return apology("A cocktail has not name")

        elif "deletebutton" in request.form:
            # No DB actions
            return render_template(
                "areyousurecocktail.html", cocktail=cocktail
            )

        elif "deleteconfirmed" in request.form:
            # Done
            cocktail_delete = request.form.get("cocktail_delete")
            amountsdeletequery = text("WITH CocktailToDelete AS \
                       (SELECT id FROM cocktails WHERE name = :name AND user_id = :user_id LIMIT 1) \
                       DELETE FROM amounts \
                       WHERE cocktail_id IN (SELECT id FROM CocktailToDelete)")
            db2.session.execute(amountsdeletequery, {"name": cocktail_delete, "user_id": session["user_id"]})
            cocktaildeletequery = text("DELETE FROM cocktails WHERE name = :name AND user_id = :user_id")
            db2.session.execute(cocktaildeletequery, {"name": cocktail_delete, "user_id": session["user_id"]})
            db2.session.commit()
            
            # db.execute("WITH CocktailToDelete AS \
            #            (SELECT id FROM cocktails WHERE name = ? AND user_id = ? LIMIT 1) \
            #            DELETE FROM amounts \
            #            WHERE cocktail_id IN (SELECT id FROM CocktailToDelete)", cocktail_delete, session["user_id"]
            #            )
            # db.execute("DELETE FROM cocktails WHERE name = ? AND user_id = ?", cocktail_delete, session["user_id"])
            # flash('Cocktail Deleted')
            return redirect(url_for("viewcocktails", _reload=int(time.time())))
        
        elif "cancel" in request.form:
            # No DB Actions
            return redirect(url_for("viewcocktails", _reload=int(time.time())))
        
        elif "close" in request.form:
            # No DB Actions
            return redirect(url_for("viewcocktails", _reload=int(time.time())))
        
        elif "changerecipe" in request.form:
            # done
            recipequery = text("SELECT id, name, build, source, family FROM cocktails WHERE name = :name AND user_id = :user_id")
            recipe = db2.session.execute(recipequery, {"name": cocktail, "user_id": session["user_id"]}).fetchone()
            # recipe = db.execute("SELECT id, name, build, source, family FROM cocktails WHERE name = ? AND user_id = ?", cocktail, session["user_id"])

            amountsquery = text("SELECT ingredient_id, amount, ingredient_source FROM amounts WHERE cocktail_id = :cocktail_id")
            amounts = db2.session.execute(amountsquery, {"cocktail_id": recipe.id}).fetchall()
            # amounts = db.execute("SELECT ingredient_id, amount, ingredient_source FROM amounts WHERE cocktail_id = ?", recipe[0]['id'])

            ingredientsquery = text("SELECT id, name, type FROM common_ingredients UNION SELECT id, name, type FROM ingredients WHERE user_id = :user_id")
            ingredients = db2.session.execute(ingredientsquery, {"user_id": session["user_id"]}).fetchall()
            # ingredients = db.execute("SELECT id, name, type FROM common_ingredients UNION SELECT id, name, type FROM ingredients WHERE user_id = ?", session["user_id"])

            # familiesquery = text()
            families = db2.session.scalars(select(CommonCocktail.family.distinct())).fetchall()
            # families = db.execute("SELECT family FROM common_cocktails GROUP BY family")
            
            types = db2.session.scalars(select(CommonIngredient.type.distinct())).fetchall()
            print(f"{types}")
            # types = db.execute("SELECT type FROM common_ingredients GROUP BY type")

            return render_template(
                "changerecipe.html", cocktail=cocktail, recipe=recipe, amounts=amounts, ingredients=ingredients, families=families, types=types
            )
        
        elif "submit-changes" in request.form:
            # done
            id = request.form.get('id')
            build = request.form.get('build')
            source = request.form.get('source')
            family = request.form.get('family')

            # update cocktail in db
            updatequery = text("UPDATE cocktails \
                       SET build = :build, \
                       source = :source, \
                       family = :family \
                       WHERE (id = :id AND user_id = :user_id)")
            db2.session.execute(updatequery, {"build": build, "source": source, "family": family, "id": id, "user_id": session["user_id"]})
            db2.session.commit()
            # db.execute("UPDATE cocktails \
            #            SET build = ?, \
            #            source = ?, \
            #            family = ? \
            #            WHERE (id = ? AND user_id = ?)"\
            #            , build, source, family, id, session["user_id"])

            # get number of rows
            amounts = request.form.getlist('amount[]')
            ingredients = request.form.getlist('ingredient[]')

            # check that amounts isn't empty
            for i in range(len(amounts)):
                if not amounts[i]:
                    return apology("amounts cannot be empty")

            # clear amounts for cocktail
            clearamounts = text("DELETE FROM amounts WHERE cocktail_id = :cocktail_id AND user_id = :user_id")
            db2.session.execute(clearamounts, {"cocktail_id": id, "user_id": session["user_id"]})
            db2.session.commit()
            # db.execute("DELETE FROM amounts WHERE cocktail_id = ? AND user_id = ?", id, session["user_id"])

            # for each table row...
            for i in range(len(amounts)):
                 # get values for amounts and ingredients
                amount = amounts[i]
                ingredient = ingredients[i]
                # get ingredient source
                id_sourcequery = text("SELECT 'common' AS source, id FROM common_ingredients \
                    WHERE name = :name \
                    UNION SELECT \
                    'user' AS source, id \
                    FROM ingredients \
                    WHERE name = :name AND user_id = :user_id")
                id_source = db2.session.execute(id_sourcequery, {"name": ingredient, "user_id": session["user_id"]}).fetchone()
                # ingredient_source = db.execute(\
                #     "SELECT 'common' AS source, id FROM common_ingredients \
                #     WHERE name = ? \
                #     UNION SELECT \
                #     'user' AS source, id \
                #     FROM ingredients \
                #     WHERE name = ? AND user_id = ?"\
                #     , ingredient, ingredient, session["user_id"])[0]['source']
                # get ingredient id
                ingredient_source = id_source.source
                ingredient_id = id_source.id   
                # ingredient_id = (db.execute("SELECT 'common' AS source, id FROM common_ingredients WHERE name = ? UNION SELECT 'user' AS source, id FROM ingredients WHERE name = ? AND user_id = ?", ingredient, ingredient, session["user_id"]))[0]['id']

                # write into database
                insertquery = text("INSERT INTO amounts (cocktail_id, ingredient_id, amount, user_id, ingredient_source) \
                           VALUES(:cocktail_id, :ingredient_id, :amount, :user_id, :ingredient_source)")
                db2.session.execute(insertquery, {"cocktail_id": id, "ingredient_id": ingredient_id, "amount": amount, "user_id": session["user_id"], "ingredient_source": ingredient_source})
                db2.session.commit()
                # db.execute("INSERT INTO amounts (cocktail_id, ingredient_id, amount, user_id, ingredient_source) \
                #            VALUES(?, ?, ?, ?, ?)", id, ingredient_id, amount, session["user_id"], ingredient_source)

            return redirect(url_for("viewcocktails", _reload=int(time.time())))


# @app.route('/debug', methods=["POST"])
    # def debug():
         #    print(f'Name: {ingredient_name} ID: {ingredient_id}, Checkbox: {value}')

