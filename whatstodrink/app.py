import os

from cs50 import SQL
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///cocktails.db")
app.config['db'] = '/cocktails.db'
# New MySQL db
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Corpse Reviver #2@localhost/whatstodrink'


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
    return render_template(
        "index.html"
    )

@app.route("/whatstodrink")
@login_required
def whatstodrink():

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
        "WHERE (a.ingredient_source = 'user' AND i.stock = 'on' AND i.user_id = ? AND c.user_id = ?) "
        "OR (a.ingredient_source = 'common' AND cs.stock = 'on' AND cs.user_id = ? AND c.user_id = ?) "
        "GROUP BY c.id "
        "HAVING COUNT(*) = (SELECT COUNT(*) FROM amounts a3 WHERE a3.cocktail_id = c.id)", session["user_id"], session["user_id"], session["user_id"], session["user_id"], session["user_id"]
    )

    ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
    amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = ?", session["user_id"])
    families = set(cocktail['family'] for cocktail in cocktails)

    return render_template(
        "whatstodrink.html", cocktails=cocktails, ingredients=ingredients, amounts=amounts, families=families
    )

@app.route("/missingone")
@login_required
def missingone():

    cocktails = db.execute(
        "SELECT cc.id, cc.name, cc.family, cc.build, cc.source "
        "FROM common_cocktails cc "
        "JOIN common_amounts ca ON cc.id = ca.cocktail_id "
        "LEFT JOIN common_ingredients ci ON ca.ingredient_id = ci.id "
        "LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id "
        "WHERE (cs.stock != 'on' AND cs.user_id = ?) "
        "GROUP BY cc.id "
        "HAVING COUNT(*) = 1 "
        "UNION "
        "SELECT c.id, c.name, c.family, c.build, c.source "
        "FROM cocktails c "
        "JOIN amounts a ON c.id = a.cocktail_id "
        "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
        "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
        "WHERE (a.ingredient_source = 'user' AND i.stock != 'on' AND i.user_id = ?) "
        "OR (a.ingredient_source = 'common' AND cs.stock != 'on' AND cs.user_id = ?) "
        "GROUP BY c.id "
        "HAVING COUNT(*) = 1", session["user_id"], session["user_id"], session["user_id"]
    )
    missing_ingredients = db.execute(
        "WITH sad_cocktails AS (\
            SELECT cc.id "
            "FROM common_cocktails cc "
            "JOIN common_amounts ca ON cc.id = ca.cocktail_id "
            "LEFT JOIN common_ingredients ci ON ca.ingredient_id = ci.id "
            "LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id "
            "WHERE (cs.stock != 'on' AND cs.user_id = ?) "
            "GROUP BY cc.id "
            "HAVING COUNT(*) = 1 "
            "UNION "
            "SELECT c.id "
            "FROM cocktails c "
            "JOIN amounts a ON c.id = a.cocktail_id "
            "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
            "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
            "WHERE (a.ingredient_source = 'user' AND i.stock != 'on' AND i.user_id = ? AND c.user_id = ?) "
            "OR (a.ingredient_source = 'common' AND cs.stock != 'on' AND cs.user_id = ? AND c.user_id = ?) "
            "GROUP BY c.id "
            "HAVING COUNT(*) = 1 \
        ), \
        sad_amounts AS (\
            SELECT ingredient_id FROM amounts WHERE (cocktail_id IN sad_cocktails AND user_id = ?)\
            UNION\
            SELECT ingredient_id FROM common_amounts WHERE cocktail_id IN sad_cocktails\
        )\
        SELECT id, name FROM ingredients WHERE (id IN sad_amounts AND stock != 'on') \
        UNION \
        SELECT ci.id, ci.name FROM common_ingredients ci \
        JOIN common_stock cs ON ci.id = cs.ingredient_id \
        WHERE (cs.stock != 'on' AND cs.user_id = ? AND ci.id IN sad_amounts) \
        GROUP BY ci.id"\
        , session["user_id"], session["user_id"], session["user_id"], session["user_id"], session["user_id"], session["user_id"], session["user_id"]
    )

    ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
    amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = ?", session["user_id"])
    return render_template(
        "missingone.html", cocktails=cocktails, ingredients=ingredients, amounts=amounts, missing_ingredients=missing_ingredients
    )
@app.route("/missingoneuser")
@login_required
def missingoneuser():

    cocktails = db.execute(
        "SELECT c.name, c.id, c.family, c.build, c.source "
        "FROM cocktails c "
        "JOIN amounts a ON c.id = a.cocktail_id "
        "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
        "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
        "WHERE (\
            (a.ingredient_source = 'user' AND i.stock != 'on' AND i.user_id = ? AND c.user_id = ?) "
            "OR \
            (a.ingredient_source = 'common' AND cs.stock != 'on' AND cs.user_id = ? AND c.user_id = ?) "
            ") \
        GROUP BY c.id "
        "HAVING COUNT(*) = 1", session["user_id"], session["user_id"], session["user_id"], session["user_id"]
    )
    print(f'cocktails missing 1: {cocktails}')

    missing_ingredients = db.execute(
        "WITH sad_cocktails AS (\
            SELECT c.id "
            "FROM cocktails c "
            "JOIN amounts a ON c.id = a.cocktail_id "
            "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
            "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
            "WHERE (\
                (a.ingredient_source = 'user' AND i.stock != 'on' AND i.user_id = ? AND c.user_id = ?) "
                "OR \
                (a.ingredient_source = 'common' AND cs.stock != 'on' AND cs.user_id = ? AND c.user_id = ?) "
                ") \
            GROUP BY c.id "
            "HAVING COUNT(*) = 1\
        ),\
        sad_amounts AS (\
            SELECT ingredient_id FROM amounts WHERE (cocktail_id IN sad_cocktails AND user_id = ?)\
            UNION\
            SELECT ingredient_id FROM common_amounts WHERE cocktail_id IN sad_cocktails\
        )\
        SELECT id, name FROM ingredients WHERE (id IN sad_amounts AND stock != 'on') \
        UNION \
        SELECT ci.id, ci.name FROM common_ingredients ci \
        JOIN common_stock cs ON ci.id = cs.ingredient_id \
        WHERE (cs.stock != 'on' AND cs.user_id = ? AND ci.id IN sad_amounts) \
        GROUP BY ci.id"\
        , session["user_id"], session["user_id"], session["user_id"], session["user_id"], session["user_id"], session["user_id"] 
    )
        
    ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
    amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = ?", session["user_id"])
    print(f'missing ingredients:{missing_ingredients}')
    return render_template(
        "missingoneuser.html", cocktails=cocktails, ingredients=ingredients, amounts=amounts, missing_ingredients=missing_ingredients
    )
  
@app.route("/whatstodrinkuser")
@login_required
def whatstodrinkuser():

    cocktails = db.execute(
        "SELECT c.name, c.id, c.family, c.build, c.source "
        "FROM cocktails c "
        "JOIN amounts a ON c.id = a.cocktail_id "
        "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
        "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
        "WHERE (a.ingredient_source = 'user' AND i.stock = 'on' AND i.user_id = ? AND c.user_id = ?) "
        "OR (a.ingredient_source = 'common' AND cs.stock = 'on' AND cs.user_id = ? AND c.user_id = ?) "
        "GROUP BY c.id "
        "HAVING COUNT(*) = (SELECT COUNT(*) FROM amounts a3 WHERE a3.cocktail_id = c.id)", session["user_id"], session["user_id"], session["user_id"], session["user_id"]
    )

    ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
    amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = ?", session["user_id"])
    families = set(cocktail['family'] for cocktail in cocktails)

    return render_template(
        "whatstodrinkuser.html", cocktails=cocktails, ingredients=ingredients, amounts=amounts, families=families
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
                "INSERT INTO ingredients (user_id, name, type, stock, short_name) VALUES(?, ?, ?, ?, ?)",
                session["user_id"],
                request.form.get("ingredientname"),
                request.form.get("type"),
                request.form.get("stock"),
                request.form.get("short-name")
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
                "INSERT INTO ingredients (user_id, name, type, stock, short_name) VALUES(?, ?, ?, ?, ?)",
                session["user_id"],
                request.form.get("ingredientname"),
                request.form.get("type"),
                request.form.get("stock"),
                request.form.get("short-name")
            )

    

        return '200: Sucess'
        
      # User reached route via GET (as by clicking a link or via redirect)
     else:
        return render_template(
            "addingredient.html"
        )

@app.route("/manageingredients", methods=["GET", "POST"])
@login_required
def manageingredients():
    
    if request.method =="GET":
        q = request.args.get('q')

        # if filter bar is used
        
        if q is not None:
            types = db.execute("SELECT DISTINCT type FROM (SELECT 'common' AS source, ci.id AS ingredient_id, ci.name, ci.type, ci.short_name, cs.stock \
                                    FROM common_ingredients ci \
                                    LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id AND cs.user_id = ? \
                                    WHERE ci.name LIKE ?\
                                    UNION SELECT 'user' AS source, i.id AS ingredient_id, i.name, i.type, i.short_name, i.stock \
                                    FROM ingredients i \
                                    WHERE i.user_id = ? AND i.name LIKE ?)", session["user_id"], '%'+q+'%', session["user_id"], '%'+q+'%')
            ingredients = db.execute("SELECT 'common' AS source, ci.id AS ingredient_id, ci.name, ci.type, ci.short_name, cs.stock, ci.notes \
                                    FROM common_ingredients ci \
                                    LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id AND cs.user_id = ? \
                                    WHERE ci.name LIKE ?\
                                    UNION SELECT 'user' AS source, i.id AS ingredient_id, i.name, i.type, i.short_name, i.stock, i.notes \
                                    FROM ingredients i \
                                    WHERE i.user_id = ? AND i.name LIKE ?\
                                    ORDER BY name ASC", session["user_id"], '%'+q+'%', session["user_id"], '%'+q+'%'
                                    )
            if request.headers.get('HX-Trigger') == 'search':
                return render_template("/ingredientstable.html", ingredients=ingredients, types=types)
            else:
                return render_template("/manageingredients.html", ingredients=ingredients, types=types)
            
        
        else:
            types = db.execute("SELECT DISTINCT type FROM common_ingredients")
            ingredients = db.execute("SELECT 'common' AS source, ci.id AS ingredient_id, ci.name, ci.type, ci.short_name, cs.stock, ci.notes \
                                     FROM common_ingredients ci \
                                     LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id AND cs.user_id = ? \
                                     UNION SELECT 'user' AS source, i.id AS ingredient_id, i.name, i.type, i.short_name, i.stock, i.notes \
                                     FROM ingredients i \
                                     WHERE i.user_id = ? \
                                     ORDER BY name ASC", session["user_id"], session["user_id"])
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
        ingredients = db.execute("SELECT name, type FROM common_ingredients UNION SELECT name, type FROM ingredients WHERE user_id = ? ORDER BY name ASC", session["user_id"])
        types = db.execute("SELECT type, COUNT(*) as type_count FROM (SELECT type FROM common_ingredients UNION SELECT DISTINCT type FROM ingredients) GROUP BY type ORDER BY type_count DESC")
        return render_template(
            "addcocktail.html", ingredients=ingredients, types=types
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
        rows = db.execute(
            "SELECT name FROM cocktails WHERE name = ? AND user_id = ? UNION SELECT name FROM common_cocktails WHERE name = ?", name, session["user_id"], name
        )
        if rows:
            return apology("You already have a cocktail by that name", 400)


        return render_template(
            "amountsmodal.html", ingredients=ingredients, build=build, source=source, family=family, name=name
        )
    
@app.route("/amounts", methods=["GET", "POST"])
@login_required
def amounts():
    # reached via post
    if request.method == "POST":
        build = request.form.get('build')
        source = request.form.get('source')
        family = request.form.get('family')
        name = request.form.get('name')

         # add cocktail to db
        db.execute(
        "INSERT INTO cocktails (name, build, source, family, user_id) VALUES(?, ?, ?, ?, ?)",
        name,
        build,
        source,
        family,
        session["user_id"]
        )

        for key, value, in request.form.items():
            if key.startswith('amount_'):
                ingredient_name = key.replace('amount_', '')
                ingredient_source = db.execute(\
                    "SELECT 'common' AS source, id FROM common_ingredients \
                    WHERE name = ? \
                    UNION SELECT \
                    'user' AS source, id \
                    FROM ingredients \
                    WHERE name = ? AND user_id = ?"\
                    , ingredient_name, ingredient_name, session["user_id"])[0]['source']
                amount = value
                ingredient_id = (db.execute("SELECT 'common' AS source, id FROM common_ingredients WHERE name = ? UNION SELECT 'user' AS source, id FROM ingredients WHERE name = ? AND user_id = ?", ingredient_name, ingredient_name, session["user_id"]))[0]['id']
                
                # get cocktail id
                cocktail_id = db.execute("SELECT id from cocktails WHERE name = ? AND user_id = ?", name, session["user_id"])[0]['id']
                #add ingredients and amounts to db
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

@app.route("/ingredientsearch")
def search():
    q = request.args.get("q")

    if q:
        results = db.execute("SELECT name FROM common_ingredients\
                             WHERE name LIKE ?\
                             UNION\
                             SELECT name FROM ingredients\
                             WHERE name LIKE ? AND user_id = ?\
                             LIMIT 10", '%'+q+'%', '%'+q+'%', session["user_id"])
    else:
        results = []

    return render_template("ingredientsearch.html", results=results)

@app.route("/modify_ingredient", methods=["GET", "POST"])
def modify_ingredient():
    ingredient = request.form.get('modifiedIngredientName')
    new_name = request.form.get('renameText')

    
    if request.method == "POST":
        if "renamebutton" in request.form:
            if new_name:
                check = db.execute("SELECT id FROM ingredients WHERE name = ? AND user_id = ? UNION SELECT id FROM common_ingredients WHERE name = ?", new_name, session["user_id"], new_name)
                if check:
                    return apology("an ingredient with that name already exists")
                else:
                    db.execute("UPDATE ingredients SET name = ? WHERE name = ? AND user_id = ?", new_name, ingredient, session["user_id"])
                    return redirect(url_for('manageingredients'))
            else:
                return apology("An ingredient has not name")
            
        elif "submitbutton" in request.form:
            newtype = request.form.get('type')
            newnotes = request.form.get('notes')
            ingredient = request.form.get('modifiedIngredientName')
            db.execute("UPDATE ingredients SET type = ?, notes = ? WHERE name = ? AND user_id = ?", newtype, newnotes, ingredient, session["user_id"])
            return redirect(url_for('manageingredients'))


        elif "deletebutton" in request.form:
            rows = db.execute("SELECT cocktails.name FROM cocktails \
                              JOIN amounts ON cocktails.id = amounts.cocktail_id \
                              LEFT JOIN ingredients ON amounts.ingredient_id = ingredients.id \
                              WHERE ingredients.name = ? \
                              GROUP BY cocktails.name", ingredient)
            if not rows:
                return render_template(
                    "areyousure.html", ingredient=ingredient
                )
            else:
                return render_template(
                    "cannotdelete.html", rows=rows, ingredient=ingredient
                )
        elif "modifybutton" in request.form:
            name = request.form.get('name')
            ingredient = db.execute("SELECT id, name, type, short_name, notes FROM ingredients WHERE name = ? AND user_id = ?", name, session["user_id"])
            types = db.execute("SELECT DISTINCT type FROM common_ingredients")
            if ingredient:
                return render_template("modifyingredient.html", ingredient=ingredient, types=types)
            else:
                return apology("Common Ingredients cannot be modified yet")
        
        elif "deleteconfirmed" in request.form:
            ingredient_delete = request.form.get("ingredient_delete")
            db.execute("DELETE FROM ingredients WHERE name = ? AND user_id = ?", ingredient_delete, session["user_id"])
            return redirect(url_for("manageingredients"))
        
        elif "cancel" in request.form:
            return redirect(url_for("manageingredients"))
        elif "close" in request.form:
            return redirect(url_for("manageingredients"))
        
  
@app.route("/viewcocktails", methods=["GET", "POST"])
def viewcocktails():
    allcocktails = db.execute(
       "SELECT 'user' AS csource, name, id, family, build, source \
        FROM cocktails \
        WHERE user_id = ? \
        UNION \
        SELECT 'common' AS csource, name, id, family, build, source \
        FROM common_cocktails", session["user_id"]
    )
    ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
    amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = ?", session["user_id"])
    allfamilies = set(cocktail['family'] for cocktail in allcocktails) 
    return render_template(
        "viewcocktails.html", allcocktails=allcocktails, ingredients=ingredients, amounts=amounts, allfamilies=allfamilies
    )

@app.route("/viewcommon")
def viewcommon():
    commoncocktails = db.execute(
        "SELECT name, id, family, build, source "
        "FROM common_cocktails "
    )
    ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
    amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = ?", session["user_id"])
    allfamilies = set(cocktail['family'] for cocktail in commoncocktails)
    
    return render_template(
        "viewcommon.html", commoncocktails=commoncocktails, ingredients=ingredients, amounts=amounts, allfamilies=allfamilies
    )
    
@app.route("/viewuser")
def viewuser():
    usercocktails = db.execute(
        "SELECT name, id, family, build, source \
        FROM cocktails \
        WHERE user_id = ?", session["user_id"]
    )
    ingredients = db.execute("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = ?", session["user_id"])
    amounts = db.execute("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = ?", session["user_id"])
    userfamilies = set(cocktail['family'] for cocktail in usercocktails)

    return render_template(
        "viewuser.html", ingredients=ingredients, amounts=amounts, userfamilies=userfamilies, usercocktails=usercocktails
    )

@app.route("/viewingredientmodal")
def viewingredientmodal():
    return render_template("viewingredientmodal.html")


@app.route("/modifycocktailmodal")
def modifycocktailmodal():
    return render_template("modifycocktailmodal.html")

@app.route("/addingredientmodal")
def addingredientmodal():
    return render_template("addingredientmodal.html")

@app.route("/modify_cocktail", methods=["GET", "POST"])
def modify_cocktail():
    cocktail = request.form.get('modifiedCocktailName')
    new_name = request.form.get('renameText')

    
    if request.method == "POST":
        if "renamebutton" in request.form:
            if new_name:
                db.execute("UPDATE cocktails SET name = ? WHERE name = ? AND user_id = ?", new_name, cocktail, session["user_id"])
                return redirect(url_for('viewcocktails'))
            else:
                return apology("A cocktail has not name")

        elif "deletebutton" in request.form:
            return render_template(
                "areyousurecocktail.html", cocktail=cocktail
            )

        elif "deleteconfirmed" in request.form:
            cocktail_delete = request.form.get("cocktail_delete")
            db.execute("WITH CocktailToDelete AS \
                       (SELECT id FROM cocktails WHERE name = ? AND user_id = ? LIMIT 1) \
                       DELETE FROM amounts \
                       WHERE cocktail_id IN (SELECT id FROM CocktailToDelete)", cocktail_delete, session["user_id"]
                       )
            db.execute("DELETE FROM cocktails WHERE name = ? AND user_id = ?", cocktail_delete, session["user_id"])
            return redirect(url_for("viewcocktails"))
        
        elif "cancel" in request.form:
            return redirect(url_for("viewcocktails"))
        
        elif "close" in request.form:
            return redirect(url_for("viewcocktails"))
        
        elif "changerecipe" in request.form:
            recipe = db.execute("SELECT id, name, build, source, family FROM cocktails WHERE name = ? AND user_id = ?", cocktail, session["user_id"])
            amounts = db.execute("SELECT ingredient_id, amount, ingredient_source FROM amounts WHERE cocktail_id = ?", recipe[0]['id'])
            ingredients = db.execute("SELECT id, name, type FROM common_ingredients UNION SELECT id, name, type FROM ingredients WHERE user_id = ?", session["user_id"])
            families = db.execute("SELECT family FROM common_cocktails GROUP BY family")
            types = db.execute("SELECT type FROM common_ingredients GROUP BY type")

            return render_template(
                "changerecipe.html", cocktail=cocktail, recipe=recipe, amounts=amounts, ingredients=ingredients, families=families, types=types
            )
        
        elif "submit-changes" in request.form:
            id = request.form.get('id')
            build = request.form.get('build')
            source = request.form.get('source')
            family = request.form.get('family')

            # update cocktail in db
            db.execute("UPDATE cocktails \
                       SET build = ?, \
                       source = ?, \
                       family = ? \
                       WHERE (id = ? AND user_id = ?)"\
                       , build, source, family, id, session["user_id"])

            # get number of rows
            amounts = request.form.getlist('amount[]')
            ingredients = request.form.getlist('ingredient[]')

            # check that amounts isn't empty
            for i in range(len(amounts)):
                if not amounts[i]:
                    return apology("amounts cannot be empty")

            # clear amounts for cocktail
            db.execute("DELETE FROM amounts WHERE cocktail_id = ? AND user_id = ?", id, session["user_id"])
            # for each table row...
            for i in range(len(amounts)):
                 # get values for amounts and ingredients
                amount = amounts[i]
                ingredient = ingredients[i]
                # get ingredient source
                ingredient_source = db.execute(\
                    "SELECT 'common' AS source, id FROM common_ingredients \
                    WHERE name = ? \
                    UNION SELECT \
                    'user' AS source, id \
                    FROM ingredients \
                    WHERE name = ? AND user_id = ?"\
                    , ingredient, ingredient, session["user_id"])[0]['source']
                # get ingredient id    
                ingredient_id = (db.execute("SELECT 'common' AS source, id FROM common_ingredients WHERE name = ? UNION SELECT 'user' AS source, id FROM ingredients WHERE name = ? AND user_id = ?", ingredient, ingredient, session["user_id"]))[0]['id']

                # write into database
                db.execute("INSERT INTO amounts (cocktail_id, ingredient_id, amount, user_id, ingredient_source) \
                           VALUES(?, ?, ?, ?, ?)", id, ingredient_id, amount, session["user_id"], ingredient_source)

            return redirect(url_for("viewcocktails"))


# @app.route('/debug', methods=["POST"])
    # def debug():
         #    print(f'Name: {ingredient_name} ID: {ingredient_id}, Checkbox: {value}')

