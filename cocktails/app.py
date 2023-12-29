import os

from cs50 import SQL
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, url_for
import logging
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from helpers import apology, login_required

# Configure application
app = Flask(__name__)

app.logger.setLevel(logging.INFO)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///cocktails.db")
app.config['db'] = '/cocktails.db'


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    cocktails = db.execute(
        "SELECT cc.name, cc.id, cc.family, cc.build, cc.source "
        "FROM common_cocktails cc "
        "JOIN common_amounts ca ON cc.id = ca.cocktail_id "
        "LEFT JOIN common_ingredients ci ON ca.ingredient_id = ci.id "
        "LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id "
        "WHERE (cs.stock = 'on' AND cs.user_id = ?) "
        "GROUP BY cc.id "
        "HAVING COUNT(*) = (SELECT COUNT(*) FROM common_amounts a2 WHERE a2.cocktail_id = cc.id) "
        "UNION "
        "SELECT c.name, c.id, c.family, c.build, c.source "
        "FROM cocktails c "
        "JOIN amounts a ON c.id = a.cocktail_id "
        "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
        "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
        "WHERE (a.ingredient_source = 'user' AND i.stock = 'on' AND i.user_id = ?) "
        "OR (a.ingredient_source = 'common' AND cs.stock = 'on' AND c.user_id = ?) "
        "GROUP BY c.id "
        "HAVING COUNT(*) = (SELECT COUNT(*) FROM amounts a3 WHERE a3.cocktail_id = c.id)", session["user_id"], session["user_id"], session["user_id"]
    )
    
    ingredients = db.execute("SELECT id, name FROM common_ingredients UNION SELECT id, name FROM ingredients")
    amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts")
    families = set(cocktail['family'] for cocktail in cocktails)
    print(f"amounts: {amounts}")
    return render_template(
        "index.html", cocktails=cocktails, ingredients=ingredients, amounts=amounts, families=families
    )
  


@app.route("/login", methods=["GET", "POST"])
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
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # make sure user has stock values for all common ingredients on login
        common_ingredients = db.execute("SELECT id FROM common_ingredients")
        # get all ids in common_ingredients
        for ingredient in common_ingredients:
            ingredient_id = ingredient['id']
            # check if user has ingredient in common_stock
            result = db.execute("SELECT ingredient_id FROM common_stock WHERE user_id = ? AND ingredient_id = ?", session["user_id"],  ingredient_id)

            # if 0, insert a default
            if len(result) == 0:
                db.execute("INSERT INTO common_stock (user_id, ingredient_id, stock) VALUES (?, ?, ?)", session["user_id"], ingredient_id, '')


        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
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
        rows = db.execute("SELECT username FROM users WHERE username = ?", uname)
        if not rows:
            # insert into users table
            hash = generate_password_hash(
                request.form.get("password"), method="pbkdf2", salt_length=16
            )
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", uname, hash)
            # assign default ingredients to stock

        else:
            return apology("username already exists", 400)
        return redirect("/")
    # if GET
    else:
        return render_template("register.html")


@app.route("/addingredient", methods=["GET", "POST"])
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
        rows = db.execute(
            "SELECT name FROM ingredients WHERE name = ? AND user_id = ? UNION SELECT name FROM common_ingredients WHERE name = ?", request.form.get("ingredientname"), session["user_id"], request.form.get("ingredientname")
        )

        # Ensure username exists and password is correct
        if rows:
            return apology("ingredient already exists", 400)
        else:
            # insert new ingredient into db
            db.execute(
                "INSERT INTO ingredients (user_id, name, type, stock) VALUES(?, ?, ?, ?)",
                session["user_id"],
                request.form.get("ingredientname"),
                request.form.get("type"),
                request.form.get("stock"),
            )
        return render_template(
            "addingredient.html"
        )
    # User reached route via GET (as by clicking a link or via redirect)
     else:
        return render_template(
            "addingredient.html"
        )

@app.route("/ingredientmodal", methods=["GET", "POST"])
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
        rows = db.execute(
            "SELECT name FROM ingredients WHERE name = ? AND user_id = ? UNION SELECT name FROM common_ingredients WHERE name = ?", request.form.get("ingredientname"), session["user_id"], request.form.get("ingredientname")
        )

        # Ensure username exists and password is correct
        if rows:
            return apology("ingredient already exists", 400)
        else:
            # insert new ingredient into db
            db.execute(
                "INSERT INTO ingredients (user_id, name, type, stock) VALUES(?, ?, ?, ?)",
                session["user_id"],
                request.form.get("ingredientname"),
                request.form.get("type"),
                request.form.get("stock"),
            )

    

        return redirect(url_for("addcocktail"))
      # User reached route via GET (as by clicking a link or via redirect)
     else:
        return render_template(
            "addingredient.html"
        )

@app.route("/manageingredients", methods=["GET", "POST"])
@login_required
def manageingredients():
    
    if request.method =="GET":
        ingredients = db.execute("SELECT 'common' AS source, ci.id AS ingredient_id, ci.name, ci.type, cs.stock FROM common_ingredients ci LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id AND cs.user_id = ? UNION SELECT 'user' AS source, i.id AS ingredient_id, i.name, i.type, i.stock FROM ingredients i WHERE i.user_id = ? ORDER BY name ASC", session["user_id"], session["user_id"])
        types = db.execute("SELECT DISTINCT type FROM common_ingredients")

        return render_template(
            "manageingredients.html", ingredients=ingredients, types=types
        )
    elif request.method =="POST":
        # set all stock to off
        db.execute(
            "UPDATE common_stock SET stock = 0 WHERE user_id = ?",
            session["user_id"]
        )
        # turn checked stock on
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

                sql_query = f"UPDATE {table_name} SET stock = ? WHERE {id_column} = ? AND user_id = ?"
            
                # Update the stock value
                db.execute(sql_query, stock, ingredient_id, session["user_id"])

                
        return redirect(url_for(
            "manageingredients"
        ))



@app.route("/addcocktail", methods=["GET", "POST"])
@login_required
def addcocktail():

    if request.method=="GET":
        ingredients = db.execute("SELECT name, type FROM common_ingredients UNION SELECT name, type FROM ingredients ORDER BY name ASC")
        types = db.execute("SELECT type, COUNT(*) as type_count FROM (SELECT type FROM common_ingredients UNION SELECT DISTINCT type FROM ingredients) GROUP BY type ORDER BY type_count DESC")
        return render_template(
            "addcocktail.html", ingredients=ingredients, types=types
        )
    
    else:
        name = request.form.get('name')
        build = request.form.get('build')
        source = request.form.get('source')
        family = request.form.get('family')
        ingredients = request.form.getlist('ingredient')
        rows = db.execute(
            "SELECT name FROM cocktails WHERE name = ? AND user_id = ? UNION SELECT name FROM common_cocktails WHERE name = ?", name, session["user_id"], name
        )
        if rows:
            return apology("You already have a cocktail by that name", 400)
        db.execute(
            "INSERT INTO cocktails (name, build, source, family, user_id) VALUES(?, ?, ?, ?, ?)",
            name,
            build,
            source,
            family,
            session["user_id"]
            )

        cocktail_id = db.execute("SELECT id from cocktails WHERE name = ? AND user_id = ?", name, session["user_id"])[0]['id']

        return render_template(
            "amounts.html", ingredients=ingredients, cocktail_id=cocktail_id
        )
    
@app.route("/amounts", methods=["GET", "POST"])
@login_required
def amounts():
    # reached via post
    if request.method == "POST":
        for key, value, in request.form.items():
            if key.startswith('amount_'):
                cocktail_id = request.form.get('cocktail_id')
                ingredient_name = key.replace('amount_', '')
                ingredient_source = db.execute("SELECT 'common' AS source, id FROM common_ingredients WHERE name = ? UNION SELECT 'user' AS source, id FROM ingredients WHERE name = ? AND user_id = ?", ingredient_name, ingredient_name, session["user_id"])[0]['source']
                amount = value
                ingredient_id = (db.execute("SELECT 'common' AS source, id FROM common_ingredients WHERE name = ? UNION SELECT 'user' AS source, id FROM ingredients WHERE name = ? AND user_id = ?", ingredient_name, ingredient_name, session["user_id"]))[0]['id']

                print(f"c.id: {cocktail_id} i.id: {ingredient_id} amount: {amount}")
                db.execute(
                    "INSERT INTO amounts (cocktail_id, ingredient_id, amount, ingredient_source, user_id) VALUES(?, ?, ?, ?, ?)",
                    cocktail_id,
                    ingredient_id,
                    amount,
                    ingredient_source,
                    session["user_id"])
    
    return render_template(
        "cocktailsuccess.html"
    )




    
# @app.route('/debug', methods=["POST"])
    # def debug():
         #    print(f'Name: {ingredient_name} ID: {ingredient_id}, Checkbox: {value}')

