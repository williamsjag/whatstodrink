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
        "SELECT c.id, c.name, c.build, c.source, c.family "
        "FROM cocktails c "
        "JOIN amounts a ON c.id = a.cocktail_id "
        "LEFT JOIN common_ingredients ci ON a.ingredient_id = ci.id "
        "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND i.user_id = ? "
        "LEFT JOIN common_cocktails cc ON c.id = cc.id "
        "WHERE "
        "("
        "(ci.id IS NOT NULL) OR "
        "(i.id IS NOT NULL AND i.stock = 'on') OR "
        "(cc.id IS NOT NULL) "
        ") "
        "GROUP BY c.id "
        "HAVING COUNT(*) = (SELECT COUNT(*) FROM amounts a2 WHERE a2.cocktail_id = c.id)",
        session["user_id"]
    )
    
    ingredients = db.execute("SELECT id, name FROM ingredients WHERE user_id = ?", session["user_id"])
    amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM AMOUNTS WHERE user_id = ?", session["user_id"])
    families = db.execute("SELECT c.family FROM cocktails c JOIN amounts a ON c.id = a.cocktail_id JOIN ingredients i ON a.ingredient_id = i.id JOIN users u ON i.user_id = u.id WHERE i.stock = 'on' AND u.id = ? GROUP BY c.id HAVING COUNT(*) = (SELECT COUNT(*) FROM amounts WHERE cocktail_id = c.id)", session["user_id"])
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
        common_ingredients = db.execute("SELECT id FROM common_ingredients").fetchall()
        # get all ids in common_ingredients
        for ingredient in common_ingredients:
            ingredient_id = ingredient['id']
            # check if user is has ingredient in common_stock
            result = db.execute("SELECT COUNT(*) FROM common_stock WHERE user_id = ? AND ingredient_id = ?", session["user_id"], ingredient_id).fetchone()

            # if 0, insert a default
            if result[0] == 0:
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
            "SELECT * FROM ingredients WHERE name = ? AND user_id = ?", request.form.get("ingredientname"), session["user_id"]
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
            "SELECT * FROM ingredients WHERE name = ? AND user_id = ?", request.form.get("ingredientname"), session["user_id"]
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

        print("ingredients data:")
        for row in ingredients:
            print(row)

        return render_template(
            "manageingredients.html", ingredients=ingredients, types=types
        )
    elif request.method =="POST":
        # set all stock to off
        db.execute(
            "UPDATE ingredients SET stock = 0 WHERE user_id = ?",
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

                print(f"Ingredient Name: {ingredient_name}")
                print(f"Ingredient ID: {ingredient_id}")
                print(f"Ingredient Source: {ingredient_source}")
                print(f"Ingredient Stock: {ingredient_stock}")

                # set stock for user ingredients
                # Determine the correct table and column for the update
                table_name = "common_stock" if ingredient_source == "common" else "ingredients"
                id_column = "ingredient_id" if ingredient_source == "common" else "id"
                stock = 'on' if ingredient_stock == 'on' else ''

                sql_query = f"UPDATE {table_name} SET stock = {stock} WHERE {id_column} = {ingredient_id} AND user_id = 6"
                print(f"SQL Query: {sql_query}")

                # Update the stock value
                db.execute(
                    "UPDATE ? SET stock = ? WHERE ? = ? AND user_id = ?",
                    table_name,
                    stock,
                    id_column,
                    ingredient_id,
                    session["user_id"]
                )

                
        return redirect(url_for(
            "manageingredients"
        ))



@app.route("/addcocktail", methods=["GET", "POST"])
@login_required
def addcocktail():

    if request.method=="GET":
        ingredients = db.execute("SELECT name, type FROM ingredients WHERE user_id = ? ORDER BY name ASC", session["user_id"])
        types = db.execute("SELECT DISTINCT type FROM ingredients WHERE user_id = ? GROUP BY type ORDER BY COUNT(type) DESC", session["user_id"])

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
            "SELECT name FROM cocktails WHERE name = ? AND user_id = ?", name, session["user_id"]
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
                amount = value
                ingredient_id = (db.execute("SELECT name, id FROM ingredients WHERE name = ? AND user_id = ?", ingredient_name, session["user_id"]))[0]['id']
                print(f"cid: {cocktail_id} ingname: {ingredient_name} amount: {amount} ing_id: {ingredient_id}")
                db.execute(
                    "INSERT INTO amounts (cocktail_id, ingredient_id, amount, user_id) VALUES(?, ?, ?, ?)",
                    cocktail_id,
                    ingredient_id,
                    amount,
                    session["user_id"])
    
    return render_template(
        "cocktailsuccess.html"
    )




    
# @app.route('/debug', methods=["POST"])
    # def debug():
         #    print(f'Name: {ingredient_name} ID: {ingredient_id}, Checkbox: {value}')

