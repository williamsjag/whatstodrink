from flask import flash, redirect, render_template, request, session, url_for
from whatstodrink import app, db
from sqlalchemy import select, union, text, or_
from werkzeug.security import check_password_hash, generate_password_hash
from whatstodrink.helpers import apology, apologynaked
from whatstodrink.models import User, Amount, Cocktail, Ingredient, CommonCocktail, CommonAmount, CommonIngredient, CommonStock, Tag, TagMapping
from whatstodrink.forms import RegistrationForm, LoginForm, ManageIngredientsForm, SettingsForm, AddIngredientForm
from flask_login import login_user, current_user, logout_user, login_required
 
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Register/Login/Logout/Account Routes


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    # Forget any user_id
    session.clear()
    form = RegistrationForm()

    if request.method == "POST":

        # check to see if user exists
        if form.validate_on_submit():
            # insert into users table
            hash = generate_password_hash(
                form.password.data, method="pbkdf2", salt_length=16
            )
            newuser = User(username=form.username.data, email=form.email.data, hash=hash, default_cocktails='on')
            db.session.add(newuser)
            db.session.commit()

            flash("Your account has been created! You are now able to log in", 'success')

            return redirect(url_for('login'))
            
        else:
            return render_template("register.html", form=form)
    
    # if GET
    else:
        return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    # Forget any user_id
    session.clear()
    form = LoginForm()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if form.validate_on_submit():
           
            # Query database for username
            uname = form.username.data
            password = form.password.data
            query = select(User).where(or_(User.username == uname, User.email == uname))
            user = db.session.scalars(query).first()

            # Ensure username exists and password is correct
            if not user or not check_password_hash(
                user.hash, password
            ):
                flash('Login failed. Double-check username and/or password', 'danger')
                return redirect(url_for('login'))

            else:
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                print(request.args)

                # Check default cocktail setting
                session["defaults"] = user.default_cocktails

                # make sure user has stock values for all common ingredients on login
                query = select(CommonIngredient.id)
                common_ingredients = db.session.scalars(query).all()

                # get all ids in common_ingredients
                for ingredient in common_ingredients:
                    # check if user has ingredient in common_stock
                    result = db.session.scalars(select(CommonStock.ingredient_id).where(CommonStock.user_id == current_user.id).where(CommonStock.ingredient_id == ingredient)).first()

                    # if not, insert a default
                    if not result:
                        newingredient = CommonStock(ingredient_id=ingredient, user_id = current_user.id, stock='')
                        db.session.add(newingredient)
                        db.session.commit()

                # Redirect user to home page
                flash("Logged In", 'primary')
                if next_page:
                    return redirect(next_page)
                else:
                    return redirect(url_for('index'))
        
        else:
            return render_template("login.html", form=form)

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    logout_user()
    flash('Logged Out', 'primary')
    # Redirect user to login form
    return redirect(url_for('login'))
    

@app.route("/account")
@login_required
def account():

    return render_template("account.html")

# About and Homepage
    

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
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

# Manage Ingredients and related routes
    

@app.route("/manageingredients", methods=["GET", "POST"])
@login_required
def manageingredients():

    form = ManageIngredientsForm()
    
    if request.method =="GET":

        # check for search queries 
        q = request.args.get('q')

        # if filter bar is used
        if q is not None:
            common_query = (
                select(CommonIngredient.type.distinct())
                .select_from(CommonIngredient)
                .outerjoin(CommonStock, (CommonIngredient.id == CommonStock.ingredient_id) & (CommonStock.user_id == current_user.id))
                .where(CommonIngredient.name.like('%' + q + '%'))
            )
            user_query = (
                select(Ingredient.type.distinct())
                .select_from(Ingredient)
                .where((Ingredient.user_id == current_user.id) & (Ingredient.name.like('%' + q + '%')))
                )
            query = union(common_query, user_query)

            types = db.session.scalars(query).all()

            ingredientsquery = text("SELECT 'common' AS source, ci.id AS ingredient_id, ci.name, ci.type, ci.short_name, cs.stock, ci.notes \
                                    FROM common_ingredients ci \
                                    LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id AND cs.user_id = :user_id \
                                    WHERE ci.name LIKE :q\
                                    UNION SELECT 'user' AS source, i.id AS ingredient_id, i.name, i.type, i.short_name, i.stock, i.notes \
                                    FROM ingredients i \
                                    WHERE i.user_id = :user_id AND i.name LIKE :q\
                                    ORDER BY name ASC")
            ingredients = db.session.execute(ingredientsquery, {"user_id": current_user.id, "q": '%'+q+'%'}).fetchall()

            if request.headers.get('HX-Trigger') == 'search':
                return render_template("/ingredientstable.html", ingredients=ingredients, types=types, form=form)
            else:
                return render_template("/manageingredients.html", ingredients=ingredients, types=types, form=form)
            
        
        else:
            typesquery = text("SELECT DISTINCT type FROM common_ingredients")
            types = db.session.execute(typesquery).fetchall()
            ingredientsquery = text("SELECT 'common' AS source, ci.id AS ingredient_id, ci.name, ci.type, ci.short_name, cs.stock, ci.notes \
                                     FROM common_ingredients ci \
                                     LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id AND cs.user_id = :user_id \
                                     UNION SELECT 'user' AS source, i.id AS ingredient_id, i.name, i.type, i.short_name, i.stock, i.notes \
                                     FROM ingredients i \
                                     WHERE i.user_id = :user_id \
                                     ORDER BY name ASC")
            ingredients = db.session.execute(ingredientsquery, {"user_id": current_user.id}).fetchall()
            return render_template(
                "manageingredients.html", ingredients=ingredients, types=types, form=form
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

                try:
                    sql_query = text(f"UPDATE {table_name} SET stock = :stock WHERE {id_column} = :ingredient_id AND user_id = :user_id")
                
                    # Update the stock value
                    db.session.execute(sql_query, {"stock": stock, "ingredient_id": ingredient_id, "user_id": current_user.id})

                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"An error occured: {e}")

                
        return redirect(url_for(
            "manageingredients", form=form
        ))
    

# View ingredient modal from ManageIngredients 
@app.route("/viewingredientmodal")
def viewingredientmodal():
    return render_template("viewingredientmodal.html")


# Modify Ingredient modal from ManageIngredients -> viewingredientmodal
@app.route("/modify_ingredient", methods=["GET", "POST"])
def modify_ingredient():
    ingredient = request.form.get('modifiedIngredientName')
    new_name = request.form.get('renameText')
    
    if request.method == "POST":

        if "renamebutton" in request.form:

            if new_name:

                checkquery = text("SELECT id FROM ingredients WHERE name = :name AND user_id = :user_id UNION SELECT id FROM common_ingredients WHERE name = :name")
                check = db.session.execute(checkquery, {"name": new_name, "user_id": current_user.id}).fetchall()

                if check:

                    return apology("an ingredient with that name already exists")
                
                else:

                    renamequery = text("UPDATE ingredients SET name = :name WHERE name = :old_name AND user_id = :user_id")
                    db.session.execute(renamequery, {"name": new_name, "old_name": ingredient, "user_id": current_user.id})
                    db.session.commit()
                    
                    # flash("Ingredient Renamed")
                    flash("Ingredient Renamed")
                    return redirect(url_for('manageingredients'))
            else:

                return apology("An ingredient has no name")
            
        elif "submitbutton" in request.form:

            newtype = request.form.get('type')
            newnotes = request.form.get('notes')
            ingredient = request.form.get('modifiedIngredientName')
            shortname = request.form.get('short_name')
            updatequery = text("UPDATE ingredients SET type = :type, notes = :notes WHERE name = :name AND user_id = :user_id")
            db.session.execute(updatequery,  {"type": newtype, "notes": newnotes, "name": ingredient, "short_name": shortname, "user_id": current_user.id})
            db.session.commit()                  

            flash("Ingredient Modified")
            return redirect(url_for('manageingredients'))


        elif "deletebutton" in request.form:
            rowsquery = text("SELECT cocktails.name FROM cocktails \
                              JOIN amounts ON cocktails.id = amounts.cocktail_id \
                              LEFT JOIN ingredients ON amounts.ingredient_id = ingredients.id \
                              WHERE ingredients.name = :name \
                              GROUP BY cocktails.name")
           
            rows = db.session.execute(rowsquery, {"name": ingredient}).fetchall()
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
            ingredientquery = text("SELECT id, name, type, short_name, notes FROM ingredients WHERE name = :name AND user_id = :user_id")
            ingredient = db.session.execute(ingredientquery, {"name": name, "user_id": current_user.id}).fetchall()

            typesquery = text("SELECT DISTINCT type FROM common_ingredients")
            types = db.session.execute(typesquery).fetchall()

            if ingredient:

                return render_template("modifyingredient.html", ingredient=ingredient, types=types)
            
            else:

                return apology("Common Ingredients cannot be modified yet")
        
        elif "deleteconfirmed" in request.form:

            ingredient_delete = request.form.get("ingredient_delete")
            deletequery = text("DELETE FROM ingredients WHERE name = :name AND user_id = :user_id")
            db.session.execute(deletequery, {"name": ingredient_delete, "user_id": current_user.id})
            db.session.commit()

            # flash('Ingredient Deleted')
            flash("Ingredient Deleted")
            return redirect(url_for("manageingredients"))
        
        # elif "cancel" in request.form:

        #     return redirect(url_for("manageingredients"))
        
        elif "close" in request.form:

            return redirect(url_for("manageingredients"))
        

# Add ingredient modal from Manage Ingredients
@app.route("/addingredientmodal2", methods=["GET", "POST"])
@login_required
def ingredientmodal2():
     
     form = AddIngredientForm()

    # reached via post
     if request.method == "POST":
        if form.validate_on_submit:
            # Ensure ingredient was submitted
            if not request.form.get("ingredientname"):
                return apology("must add ingredient", 400)

            # Ensure type was submitted
            elif not request.form.get("type"):
                return apology("must select ingredient type", 400)

            # Query database for ingredient
            rowsquery = text("SELECT name FROM ingredients WHERE name = :ingredientname AND user_id = :user_id UNION SELECT name FROM common_ingredients WHERE name = :ingredientname")
            rows = db.session.execute(rowsquery, {"ingredientname": request.form.get("ingredientname"), "user_id": current_user.id}).fetchall()

            # Ensure username exists and password is correct
            if rows:
                return apology("ingredient already exists", 400)
            else:
                # insert new ingredient into db
                new_ingredient = Ingredient(
                    user_id=current_user.id,
                    name=request.form.get("ingredientname"),
                    type=request.form.get("type"),
                    stock=request.form.get("stock"),
                    short_name=request.form.get("short-name"),
                    notes=request.form.get("notes"),
                )
                db.session.add(new_ingredient)
                db.session.commit()    
                
            flash("Ingredient Added")
            return redirect(url_for("manageingredients"))
        else:
            render_template("addingredient.html", form=form)
        
     # User reached route via GET (as by clicking a link or via redirect)
     else:
        return render_template(
            "addingredientmodal2.html", form=form
        )


# AddIngredient/AddCocktail/Amounts and related routes


@app.route("/addingredient", methods=["GET", "POST"])
@login_required
def addingredient():

    form = AddIngredientForm()

    # reached via post
    if request.method == "POST":
        if form.validate_on_submit():
            # insert new ingredient into db
            newingredient = Ingredient(name=form.name.data, short_name=form.short_name.data, type=form.type.data, notes=form.notes.data, stock=form.stock.data, user_id=current_user.id)
            db.session.add(newingredient)
            db.session.commit()
            
            flash('Ingredient Added', 'primary')

            return render_template(
                "addingredient.html", form=form
            )
        else:
            return render_template('addingredient.html', form=form)
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template(
            "addingredient.html", form=form
        )
    

@app.route("/addcocktail", methods=["GET", "POST"])
@login_required
def addcocktail():

    if request.method=="GET":
       
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
            return apologynaked("every good cocktail has a name", 403)
        if not ingredients:
            return apologynaked("an empty glass is not a cocktail", 403)
        rowsquery = text("SELECT name FROM cocktails WHERE name = :name AND user_id = :user_id")
        rows = db.session.execute(rowsquery, {"name": name, "user_id": current_user.id}).fetchall()
        
        if rows:
            return apology("You already have a cocktail by that name", 403)


        return render_template(
            "amountsmodal.html", ingredients=ingredients, build=build, source=source, family=family, name=name
        )
    

# Ingredient Search Box from Add Cocktail
@app.route("/ingredientsearch")
def ingredientsearch():
    q = request.args.get("q")

    if q:
        resultsquery = text("SELECT name FROM common_ingredients\
                             WHERE name LIKE :q\
                             UNION\
                             SELECT name FROM ingredients\
                             WHERE name LIKE :q AND user_id = :user_id\
                             LIMIT 10")
        results = db.session.execute(resultsquery, {"q": '%'+q+'%', "user_id": current_user.id}).fetchall()
        
    else:
        results = []

    return render_template("ingredientsearch.html", results=results)


# Create New Ingredient modal from Add Cocktail
@app.route("/addingredientmodal", methods=["GET", "POST"])
def addingredientmodal():
    if request.method == "GET":
        return render_template("addingredientmodal.html")
    else:
        # Ensure ingredient was submitted
        if not request.form.get("ingredientname"):
            return apology("must add ingredient", 400)

        # Ensure type was submitted
        elif not request.form.get("type"):
            return apology("must select ingredient type", 400)

        # Query database for ingredient
        rowsquery = text("SELECT name FROM ingredients WHERE name = :name AND user_id = :user_id UNION SELECT name FROM common_ingredients WHERE name = :name")
        rows = db.session.execute(rowsquery, {"name": request.form.get("ingredientname"), "user_id": current_user.id}).fetchall()

        # Ensure username exists and password is correct
        if rows:
            return apology("ingredient already exists", 400)
        else:
            # insert new ingredient into db
            insertquery = text("INSERT INTO ingredients (user_id, name, type, stock, short_name, notes) VALUES(:user_id, :name, :type, :stock, :short_name, :notes)")
            db.session.execute(insertquery, {"user_id": current_user.id, "name": request.form.get("ingredientname"), "type": request.form.get("type"), "stock": request.form.get("stock"), "short_name": request.form.get("short-name"), "notes": request.form.get("notes)")})
            db.session.commit()
        
            # flash('Ingredient Added')
            return "200"


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
        addquery = text("INSERT INTO cocktails (name, build, source, family, user_id) VALUES(:name, :build, :source, :family, :user_id)")
        db.session.execute(addquery, {"name": name, "build": build, "source": source, "family": family, "user_id": current_user.id})
        db.session.commit()

        for key, value, in request.form.items():
            if key.startswith('amount_'):
                ingredient_name = key.replace('amount_', '')
                sourcequery = text("SELECT 'common' AS source, id FROM common_ingredients \
                    WHERE name = :name \
                    UNION SELECT \
                    'user' AS source, id \
                    FROM ingredients \
                    WHERE name = :name AND user_id = :user_id")
                id_source = db.session.execute(sourcequery, {"name": ingredient_name, "user_id": current_user.id}).fetchone()
                
                amount = value
               
                # get cocktail id
                c_id_query = text("SELECT id FROM cocktails WHERE name = :name AND user_id = :user_id")
                cocktail_id = db.session.scalar(c_id_query, {"name": name, "user_id": current_user.id})
                
                #add ingredients and amounts to db
                insertquery = text("INSERT INTO amounts (cocktail_id, ingredient_id, amount, ingredient_source, user_id) VALUES(:cocktail_id, :ingredient_id, :amount, :ingredient_source, :user_id)")
                db.session.execute(insertquery, {"cocktail_id": cocktail_id, "ingredient_id": id_source.id, "amount": amount, "ingredient_source": id_source.source, "user_id": current_user.id})
                db.session.commit()
                
    flash('Cocktail Added')
    return redirect(url_for(
        "addcocktail"
    ))


# Viewall and related routes
  
@app.route("/viewcocktails", methods=["GET", "POST"])
def viewcocktails():

    return render_template(
        "viewcocktails.html", defaults=session["defaults"]
    )

@app.route("/viewallcocktails")
def viewallcocktails():

    allquery = text("SELECT 'user' AS csource, name, id, family, build, source \
        FROM cocktails \
        WHERE user_id = :user_id \
        UNION \
        SELECT 'common' AS csource, name, id, family, build, source \
        FROM common_cocktails")

    allcocktails = db.session.execute(allquery, {"user_id": current_user.id}).fetchall()
    
    ingredientsquery = text("\
                            WITH allingredients AS (\
                                SELECT id, name, short_name FROM common_ingredients \
                                UNION \
                                SELECT id, name, short_name FROM ingredients \
                                WHERE user_id = :user_id), \
                            usedingredients AS (\
                                SELECT ingredient_id FROM common_amounts\
                                UNION select ingredient_id FROM amounts WHERE user_id = :user_id) \
                            SELECT id, name, short_name FROM allingredients INNER JOIN usedingredients ON allingredients.id = usedingredients.ingredient_id")
    ingredients = db.session.execute(ingredientsquery, {"user_id": current_user.id}).fetchall()

    amountsquery = text("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = :user_id")
    amounts = db.session.execute(amountsquery, {"user_id": current_user.id}).fetchall()

    allfamilies = set(Cocktail.family for Cocktail in allcocktails)

    return render_template(
        "viewallcocktails.html", allcocktails=allcocktails, ingredients=ingredients, amounts=amounts, allfamilies=allfamilies, defaults=session["defaults"]
    )

# Modify cocktail modal from viewallcocktails
@app.route("/modifycocktailmodal")
def modifycocktailmodal():
    return render_template("modifycocktailmodal.html")

@app.route("/viewcommon")
def viewcommon():

    commoncocktailsquery = text(
        "SELECT name, id, family, build, source "
        "FROM common_cocktails "
    )
    commoncocktails = db.session.execute(commoncocktailsquery).fetchall()

    ingredientsquery = text("WITH allingredients AS \
                                (SELECT id, name, short_name FROM common_ingredients), \
                            usedingredients AS \
                                (SELECT ingredient_id FROM common_amounts)\
                            SELECT id, name, short_name FROM allingredients WHERE id IN (SELECT ingredient_id FROM usedingredients)")
    ingredients = db.session.execute(ingredientsquery).fetchall()

    amountsquery = text("SELECT cocktail_id, ingredient_id, amount FROM common_amounts")
    amounts = db.session.execute(amountsquery).fetchall()

    allfamilies = set(Cocktail.family for Cocktail in commoncocktails)
    
    return render_template(
        "viewcommon.html", commoncocktails=commoncocktails, ingredients=ingredients, amounts=amounts, allfamilies=allfamilies
    )

# Change Recipe modal from viewallcocktails->modifycocktailmodal 
@app.route("/modify_cocktail", methods=["GET", "POST"])
def modify_cocktail():
    cocktail = request.form.get('modifiedCocktailName')
    new_name = request.form.get('renameText')

    
    if request.method == "POST":
        if "renamebutton" in request.form:
            if new_name:
                rowsquery = text("SELECT name FROM cocktails WHERE name = :new_name AND user_id = :user_id")
                rows = db.session.execute(rowsquery, {"new_name": new_name, "user_id": current_user.id}).fetchall()
                
                if rows:
                    return apology("You already have a cocktail by that name", 400)
                else:
                    update = text("UPDATE cocktails SET name = :new_name WHERE name = :cocktail AND user_id = :user_id")
                    db.session.execute(update, {"new_name": new_name, "cocktail": cocktail, "user_id": current_user.id})
                    db.session.commit()
                    flash("Cocktail Renamed")
                    return redirect(url_for('viewcocktails'))
            else:
                return apology("A cocktail has not name")

        elif "deletebutton" in request.form:
            return render_template(
                "areyousurecocktail.html", cocktail=cocktail
            )

        elif "deleteconfirmed" in request.form:
            cocktail_delete = request.form.get("cocktail_delete")
            amountsdeletequery = text("WITH CocktailToDelete AS \
                       (SELECT id FROM cocktails WHERE name = :name AND user_id = :user_id LIMIT 1) \
                       DELETE FROM amounts \
                       WHERE cocktail_id IN (SELECT id FROM CocktailToDelete)")
            db.session.execute(amountsdeletequery, {"name": cocktail_delete, "user_id": current_user.id})
            cocktaildeletequery = text("DELETE FROM cocktails WHERE name = :name AND user_id = :user_id")
            db.session.execute(cocktaildeletequery, {"name": cocktail_delete, "user_id": current_user.id})
            db.session.commit()
            
            flash('Cocktail Deleted')
            return redirect(url_for("viewcocktails"))
        
        elif "changerecipe" in request.form:
            recipequery = text("SELECT id, name, build, source, family FROM cocktails WHERE name = :name AND user_id = :user_id")
            recipe = db.session.execute(recipequery, {"name": cocktail, "user_id": current_user.id}).fetchone()

            amountsquery = text("SELECT ingredient_id, amount, ingredient_source FROM amounts WHERE cocktail_id = :cocktail_id")
            amounts = db.session.execute(amountsquery, {"cocktail_id": recipe.id}).fetchall()

            ingredientsquery = text("SELECT id, name, type FROM common_ingredients UNION SELECT id, name, type FROM ingredients WHERE user_id = :user_id")
            ingredients = db.session.execute(ingredientsquery, {"user_id": current_user.id}).fetchall()

            families = db.session.scalars(select(CommonCocktail.family.distinct())).fetchall()
            
            types = db.session.scalars(select(CommonIngredient.type.distinct())).fetchall()

            flash("Recipe Modified")
            return render_template(
                "changerecipe.html", cocktail=cocktail, recipe=recipe, amounts=amounts, ingredients=ingredients, families=families, types=types
            )
        
        elif "submit-changes" in request.form:
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
            db.session.execute(updatequery, {"build": build, "source": source, "family": family, "id": id, "user_id": current_user.id})
            db.session.commit()

            # get number of rows
            amounts = request.form.getlist('amount[]')
            ingredients = request.form.getlist('ingredient[]')

            # check that amounts isn't empty
            for i in range(len(amounts)):
                if not amounts[i]:
                    return apology("amounts cannot be empty")

            # clear amounts for cocktail
            clearamounts = text("DELETE FROM amounts WHERE cocktail_id = :cocktail_id AND user_id = :user_id")
            db.session.execute(clearamounts, {"cocktail_id": id, "user_id": current_user.id})
            db.session.commit()

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
                id_source = db.session.execute(id_sourcequery, {"name": ingredient, "user_id": current_user.id}).fetchone()
                
                ingredient_source = id_source.source
                ingredient_id = id_source.id   

                # write into database
                insertquery = text("INSERT INTO amounts (cocktail_id, ingredient_id, amount, user_id, ingredient_source) \
                           VALUES(:cocktail_id, :ingredient_id, :amount, :user_id, :ingredient_source)")
                db.session.execute(insertquery, {"cocktail_id": id, "ingredient_id": ingredient_id, "amount": amount, "user_id": current_user.id, "ingredient_source": ingredient_source})
                db.session.commit()

            return redirect(url_for("viewcocktails"))
        

@app.route("/viewuser")

def viewuser():

    cocktailquery = text("SELECT name, id, family, build, source \
                        FROM cocktails \
                        WHERE user_id = :user_id")
   
    usercocktails = db.session.execute(cocktailquery, {"user_id": current_user.id}).fetchall()
    print(f"{usercocktails}")
   
    ingredientsquery = text("WITH allingredients AS (\
                                SELECT id, name, short_name FROM common_ingredients \
                                UNION \
                                SELECT id, name, short_name FROM ingredients \
                                WHERE user_id = :user_id), \
                            usedingredients AS (\
                                SELECT ingredient_id FROM amounts WHERE user_id = :user_id) \
                            SELECT id, name, short_name FROM allingredients WHERE id IN (SELECT ingredient_id FROM usedingredients)")
    ingredients = db.session.execute(ingredientsquery, {"user_id": current_user.id}).fetchall()
        
    amountsquery = text("SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = :user_id")
    amounts = db.session.execute(amountsquery, {"user_id": current_user.id}).fetchall()
    userfamilies = set(Cocktail.family for Cocktail in usercocktails)

    return render_template(
        "viewuser.html", ingredients=ingredients, amounts=amounts, usercocktails=usercocktails, userfamilies=userfamilies
    )


# Missingone and related routes

@app.route("/missingone")
@login_required
def missingone():
   
    return render_template(
        "missingone.html", defaults=session["defaults"]
    )

@app.route("/missingoneall")
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
    cocktails = db.session.execute(cocktailsquery, {"user_id": current_user.id}).fetchall()

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
            SELECT ingredient_id FROM amounts WHERE (cocktail_id IN (SELECT id FROM sad_cocktails) AND user_id = :user_id)\
            UNION\
            SELECT ingredient_id FROM common_amounts WHERE cocktail_id IN (SELECT id FROM sad_cocktails)\
        )\
        SELECT id, name FROM ingredients WHERE (id IN (SELECT ingredient_id FROM sad_amounts) AND stock != 'on') \
        UNION \
        SELECT ci.id, ci.name FROM common_ingredients ci \
        JOIN common_stock cs ON ci.id = cs.ingredient_id \
        WHERE (cs.stock != 'on' AND cs.user_id = :user_id AND ci.id IN (SELECT ingredient_id FROM sad_amounts)) \
        GROUP BY ci.id")
    missing_ingredients = db.session.execute(missingquery, {"user_id": current_user.id}).fetchall()
   
    ingredientsquery = text("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = :user_id")
    ingredients = db.session.execute(ingredientsquery, {"user_id": current_user.id}).fetchall()
   
    amountsquery = text("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = :user_id")
    amounts = db.session.execute(amountsquery, {"user_id": current_user.id}).fetchall()

    return render_template(
        "missingoneall.html", cocktails=cocktails, ingredients=ingredients, amounts=amounts, missing_ingredients=missing_ingredients, defaults=session["defaults"]
    )

@app.route("/missingoneuser")
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
    cocktails = db.session.execute(cocktailquery, {"user_id": current_user.id}).fetchall()

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
            SELECT ingredient_id FROM amounts WHERE (cocktail_id IN (SELECT id FROM sad_cocktails) AND user_id = :user_id)\
            UNION\
            SELECT ingredient_id FROM common_amounts WHERE cocktail_id IN (SELECT id FROM sad_cocktails)\
        )\
        SELECT id, name FROM ingredients WHERE (id IN (SELECT ingredient_id FROM sad_amounts) AND stock != 'on') \
        UNION \
        SELECT ci.id, ci.name FROM common_ingredients ci \
        JOIN common_stock cs ON ci.id = cs.ingredient_id \
        WHERE (cs.stock != 'on' AND cs.user_id = :user_id AND ci.id IN (SELECT ingredient_id FROM sad_amounts)) \
        GROUP BY ci.id")
    missing_ingredients = db.session.execute(missingquery, {"user_id": current_user.id}).fetchall()
    
    ingredientsquery = text("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = :user_id")
    ingredients = db.session.execute(ingredientsquery, {"user_id": current_user.id}).fetchall()
   
    amountsquery = text("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = :user_id")
    amounts = db.session.execute(amountsquery, {"user_id": current_user.id}).fetchall()

    return render_template(
        "missingoneuser.html", cocktails=cocktails, ingredients=ingredients, amounts=amounts, missing_ingredients=missing_ingredients
    )
    

# Whatstodrink and Related Routes 

@app.route("/whatstodrink")
@login_required
def whatstodrink():

    return render_template(
        "whatstodrink.html", defaults=session["defaults"]
    )


@app.route("/whatstodrinkuser")
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
    cocktails = db.session.execute(cocktailsquery, {"user_id": current_user.id}).fetchall()

    ingredientsquery = text("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = :user_id")
    ingredientsquery = text("WITH allingredients AS \
                                (SELECT id, name, short_name FROM common_ingredients \
                                UNION SELECT id, name, short_name FROM ingredients WHERE user_id = :user_id), \
                            amounts AS \
                                (SELECT ingredient_id FROM amounts WHERE user_id = :user_id) \
                            SELECT id, name, short_name FROM allingredients INNER JOIN amounts ON allingredients.id = amounts.ingredient_id\
                        ")
    ingredients = db.session.execute(ingredientsquery, {"user_id": current_user.id}).fetchall()
   
    amountsquery = text("SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = :user_id")
    amounts = db.session.execute(amountsquery, {"user_id": current_user.id}).fetchall()

    families = set(Cocktail.family for Cocktail in cocktails)

    return render_template(
        "whatstodrinkuser.html", cocktails=cocktails, ingredients=ingredients, amounts=amounts, families=families
    )


@app.route("/whatstodrinkall")
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
    cocktails = db.session.execute(cocktailquery, {"user_id": current_user.id}).fetchall()
   
    # ingredientsquery = text("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = :user_id")
    ingredientsquery = text("WITH allingredients AS \
                                (SELECT id, name, short_name FROM common_ingredients \
                                UNION SELECT id, name, short_name FROM ingredients WHERE user_id = :user_id), \
                            amounts AS \
                                (SELECT ingredient_id FROM amounts WHERE user_id = :user_id \
                                UNION SELECT ingredient_id FROM common_amounts)\
                            SELECT id, name, short_name FROM allingredients INNER JOIN amounts ON allingredients.id = amounts.ingredient_id\
                        ")
    ingredients = db.session.execute(ingredientsquery, {"user_id": current_user.id}).fetchall()
        
    amountsquery = text("SELECT cocktail_id, ingredient_id, amount FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount FROM amounts WHERE user_id = :user_id")
    amounts = db.session.execute(amountsquery, {"user_id": current_user.id}).fetchall()

    families = set(Cocktail.family for Cocktail in cocktails)

    return render_template(
        "whatstodrinkall.html", cocktails=cocktails, ingredients=ingredients, amounts=amounts, families=families
        )

