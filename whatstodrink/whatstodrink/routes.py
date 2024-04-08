from flask import flash, redirect, render_template, request, session, url_for, Response
from whatstodrink import app, db
from sqlalchemy import select, union, text, or_, update
from werkzeug.security import check_password_hash, generate_password_hash
from whatstodrink.helpers import apology, apologynaked
from whatstodrink.models import User, Amount, Cocktail, Ingredient, CommonCocktail, CommonAmount, CommonIngredient, CommonStock, Tag, TagMapping
from whatstodrink.forms import RegistrationForm, LoginForm, ManageIngredientsForm, SettingsForm, AddIngredientForm, AddCocktailForm, ViewIngredientForm, ModifyIngredientForm, DeleteForm, ModifyCocktailForm
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
                flash("Successfully logged in, welcome {}!".format(user.username), 'primary')
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

        # if filter bar is entered
        if q is not None:
            # Get Types included in search for headers
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

            types = db.session.execute(query).all()

            # Get ingredients that match
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
                stock = 1 if ingredient_stock == 'on' else 0

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

    form = ViewIngredientForm()

    for key, value, in request.args.items():
        if key.startswith('stock_'):
            ingredient_name = key.replace('stock_', '')
        # contingency if stock not checked
        elif key.startswith('id_'):
            ingredient_name = key.replace('id_', '')
            
    ingredient = db.session.execute(select(Ingredient).where(Ingredient.name == ingredient_name).where(Ingredient.user_id == current_user.id)).fetchone()
    ingredient = ingredient[0]

    return render_template("viewingredientmodal.html", form=form, ingredient=ingredient)


# Modify Ingredient modal from ManageIngredients -> viewingredientmodal
@app.route("/modify_ingredient", methods=["GET", "POST"])
def modify_ingredient():

    form = ViewIngredientForm()
    ingredient = form.name.data
    
    if request.method == "POST":
            
        if "submitbutton" in request.form:
            
            form = ModifyIngredientForm()

            id = form.id.data
            newtype = form.type.data
            newnotes = form.notes.data
            newname = form.name.data
            shortname = form.short_name.data
        
            updatequery = text("UPDATE ingredients SET type = :type, notes = :notes, name = :name, short_name = :short_name WHERE id = :id AND user_id = :user_id")
            db.session.execute(updatequery,  {"id": id, "type": newtype, "notes": newnotes, "name": newname, "short_name": shortname, "user_id": current_user.id})
            db.session.commit()   

            # Check for cocktails using this ingredient
            query = text("""
                         SELECT cocktail_id
                         FROM amounts
                         WHERE ingredient_id = :id AND ingredient_source = 'user'
                         """)
            cocktails = db.session.scalars(query, {"id": id}).fetchall()

            for cocktail in cocktails:
                ingredientsq = text("""
                                   SELECT * FROM (
                                        SELECT i.id, i.name, i.short_name, 'user' AS source, a.sequence
                                        FROM ingredients i
                                        LEFT JOIN amounts a ON i.id = a.ingredient_id
                                        WHERE a.ingredient_source = 'user' AND a.cocktail_id = :cocktail AND a.user_id = :user_id
                                        
                                        UNION
                                        
                                        SELECT ci.id, ci.name, ci.short_name, 'common' AS source, aa.sequence
                                        FROM common_ingredients ci
                                        LEFT JOIN amounts aa ON ci.id = aa.ingredient_id
                                        WHERE aa.ingredient_source = 'common' AND aa.cocktail_id = :cocktail AND aa.user_id = :user_id
                                    ) AS combined_ingredients
                                    ORDER BY sequence ASC;
                                    """)
                ingredients = db.session.execute(ingredientsq, {"user_id": current_user.id, "cocktail": cocktail}).fetchall()
                amountsq = text("""
                                SELECT ingredient_id, amount, cocktail_id, sequence
                                FROM amounts
                                WHERE cocktail_id = :cocktail AND user_id = :user_id
                                ORDER BY sequence ASC
                                """)
                amounts = db.session.execute(amountsq, {"cocktail": cocktail, "user_id": current_user.id}).fetchall()

                recipe = ""
                for amount, ingredient in zip(amounts, ingredients):
                    recipe += f"{amount.amount} {ingredient.name}\n"
                
                ingredient_list = ', '.join([row.short_name if row.short_name else row.name for row in ingredients])
                
                db.session.execute(
                    update(Cocktail).where(Cocktail.id == cocktail)
                    .where(Cocktail.user_id == current_user.id)
                    .values(recipe=recipe, 
                            ingredient_list=ingredient_list))
                db.session.commit()

            flash("Ingredient Modified", "primary")
            return redirect(url_for('manageingredients'))


        elif "deletebutton" in request.form:

            form = DeleteForm()

            ingredientId = db.session.scalar(select(Ingredient.id).where(Ingredient.name == ingredient).where(Ingredient.user_id == current_user.id))

            query = text("""
                         SELECT cocktail_id
                         FROM amounts
                         WHERE ingredient_id = :id AND ingredient_source = 'user'
                         """)

            cocktails = db.session.scalars(query, {"id": ingredientId}).fetchall()

            if not cocktails:

                return render_template(
                    "areyousure.html", ingredient=ingredient, form=form, ingredientId=ingredientId
                )
            
            else:
                
                rows = db.session.scalars(select(Cocktail.name).where(Cocktail.id.in_(cocktails))).fetchall()

                return render_template(
                    "cannotdelete.html", rows=rows, ingredient=ingredient, form=form
                )
            
        elif "modifybutton" in request.form:

            form = ViewIngredientForm()

            name = form.name.data
            ingredientquery = text("SELECT id, name, type, short_name, notes FROM ingredients WHERE name = :name AND user_id = :user_id")
            ingredient = db.session.execute(ingredientquery, {"name": name, "user_id": current_user.id}).fetchall()

            typesquery = text("SELECT DISTINCT type FROM common_ingredients")
            types = db.session.execute(typesquery).fetchall()

            form = ModifyIngredientForm()

            if ingredient:

                return render_template("modifyingredient.html", ingredient=ingredient[0], types=types, form=form)
            
            else:

                return apology("Common Ingredients cannot be modified yet")
        
        elif "deleteconfirmed" in request.form:

            form = DeleteForm()

            ingredient_delete = form.id.data

            deletequery = text("DELETE FROM ingredients WHERE id = :id AND user_id = :user_id")
            db.session.execute(deletequery, {"id": ingredient_delete, "user_id": current_user.id})
            db.session.commit()

            flash("Ingredient Deleted", "danger")
            return redirect(url_for("manageingredients"))
        
        # elif "cancel" in request.form:

        #     return redirect(url_for("manageingredients"))
        
        elif "close" in request.form:

            return redirect(url_for("manageingredients"))
        

# Add ingredient modal from Manage Ingredients
@app.route("/addingredientmodal2", methods=["GET", "POST"])
@login_required
def addingredientmodal2():
     
    form = AddIngredientForm()

    # reached via post
    if request.method == "POST":
        if form.validate_on_submit:

            # Query database for ingredient
            rowsquery = text("SELECT name FROM ingredients WHERE name = :ingredientname AND user_id = :user_id")
            rows = db.session.execute(rowsquery, {"ingredientname": request.form.get("ingredientname"), "user_id": current_user.id}).fetchall()

            # Ensure username exists and password is correct
            if rows:
                return apology("ingredient already exists", 403)
            else:
                # insert new ingredient into db
                new_ingredient = Ingredient(
                    user_id=current_user.id,
                    name=form.name.data,
                    type=form.type.data,
                    stock=form.stock.data,
                    short_name=form.short_name.data,
                    notes=form.notes.data,
                )
                db.session.add(new_ingredient)
                db.session.commit()    
                
            flash("Ingredient Added", "primary")
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

    form = AddCocktailForm()

    if request.method=="GET":
       
        return render_template(
            "addcocktail.html", form=form
        )
    
    else:
        if form.validate_on_submit():

            
            # Get list of amounts
            rawamounts = request.form.getlist('amount')
            amounts = list(filter(None, rawamounts))
            # Get list of ingredients
            rawingredients = request.form.getlist('q')
            ingredients = list(filter(None, rawingredients))

            if not ingredients:
                return apology("an empty glass is not a cocktail", 403)
            
            # Check for existing cocktail
            rowsquery = text("SELECT name FROM cocktails WHERE name = :name AND user_id = :user_id")
            rows = db.session.execute(rowsquery, {"name": form.name.data, "user_id": current_user.id}).fetchall()
            
            if rows:
                return apology("You already have a cocktail by that name", 403)
            else:
               
                recipe = ""
                for amount, ingredient in zip(amounts, ingredients):
                    # concatenate amount/ingredient, and newline
                    recipe += f"{amount} {ingredient}\n"
                
                # Add cocktail to db
                newcocktail = Cocktail(name=form.name.data, 
                                       build=form.build.data, 
                                       source=form.source.data, 
                                       user_id=current_user.id, 
                                       family=form.family.data, 
                                       notes=form.notes.data,
                                       recipe=recipe
                                       )
                db.session.add(newcocktail)
                db.session.commit()

                # Find id for new cocktail
                cocktail_id = db.session.scalar(select(Cocktail.id).where(Cocktail.name == form.name.data).where(Cocktail.user_id == current_user.id))

                # Add amounts to db
                # get source for ingredients
                counter = 1
                for amount, ingredient in zip(amounts, ingredients):
                    sourcequery = text("SELECT 'common' AS source, id, short_name, name FROM common_ingredients \
                        WHERE name = :name \
                        UNION SELECT \
                        'user' AS source, id, short_name, name \
                        FROM ingredients \
                        WHERE name = :name AND user_id = :user_id")
                    id_source = db.session.execute(sourcequery, {"name": ingredient, "user_id": current_user.id}).fetchone()
                    insertquery = text("INSERT INTO amounts (cocktail_id, ingredient_id, amount, ingredient_source, user_id, sequence) VALUES(:cocktail_id, :ingredient_id, :amount, :ingredient_source, :user_id, :counter)")
                    db.session.execute(insertquery, {"cocktail_id": cocktail_id, "ingredient_id": id_source.id, "amount":amount, "ingredient_source":id_source.source, "user_id": current_user.id, "counter": counter})
                    db.session.commit()
                    counter += 1

                recipequery = text("""
                                   SELECT * FROM (
                                        SELECT i.name, i.short_name, a.sequence
                                        FROM ingredients i
                                        LEFT JOIN amounts a ON i.id = a.ingredient_id
                                        WHERE a.cocktail_id = :cocktail AND a.user_id = :user_id
                                        
                                        UNION
                                        
                                        SELECT ci.name, ci.short_name, aa.sequence
                                        FROM common_ingredients ci
                                        LEFT JOIN amounts aa ON ci.id = aa.ingredient_id
                                        WHERE aa.cocktail_id = :cocktail AND aa.user_id = :user_id
                                    ) AS combined_ingredients
                                    ORDER BY sequence ASC; 
                                   """)
                reciperesults = db.session.execute(recipequery, {"user_id": current_user.id, "cocktail": cocktail_id}).fetchall()
                ingredient_list = ', '.join([row.short_name if row.short_name else row.name for row in reciperesults])
              
                db.session.execute(
                    update(Cocktail).where(Cocktail.id == cocktail_id)
                    .where(Cocktail.user_id == current_user.id)
                    .values(ingredient_list=ingredient_list)
                )
                db.session.commit()


            flash("Cocktail Added", 'primary')
            return redirect(url_for(
                "addcocktail"
            ))
        
        else:
            return render_template(
                "addcocktail.html", form=form
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

    form = AddIngredientForm()

    if request.method == "GET":
        return render_template("addingredientmodal.html", form=form)
    else:
        # Ensure ingredient was submitted
        if form.validate_on_submit:

            # Query database for ingredient
            rowsquery = text("SELECT name FROM ingredients WHERE name = :ingredientname AND user_id = :user_id")
            rows = db.session.execute(rowsquery, {"ingredientname": request.form.get("ingredientname"), "user_id": current_user.id}).fetchall()

            # Ensure username exists and password is correct
            if rows:
                return apology("ingredient already exists", 403)
            else:
                # insert new ingredient into db
                new_ingredient = Ingredient(
                    user_id=current_user.id,
                    name=form.name.data,
                    type=form.type.data,
                    stock=form.stock.data,
                    short_name=form.short_name.data,
                    notes=form.notes.data,
                )
                db.session.add(new_ingredient)
                db.session.commit()    

            return form.name.data
        else:
            return (render_template("addingredient.html", form=form))

# Viewall and related routes
  
@app.route("/viewcocktails", methods=["GET", "POST"])
def viewcocktails():

    return render_template(
        "viewcocktails.html", defaults=session["defaults"]
    )

@app.route("/viewallcocktails")
def viewallcocktails():

    form = ModifyCocktailForm()

    userquery = text("""       
                    SELECT 'user' AS csource, name, id, family, build, source, recipe, ingredient_list, notes \
                    FROM cocktails
                    WHERE user_id = :user_id
                    UNION               
                    SELECT 'common' AS csource, name, id, family, build, source, recipe, ingredient_list, NULL AS notes \
                    FROM common_cocktails   
        """)

    allcocktails = db.session.execute(userquery, {"user_id": current_user.id}).fetchall()
    
    familyquery = text("SELECT DISTINCT family FROM cocktails UNION SELECT DISTINCT family FROM common_cocktails")
    allfamilies = db.session.scalars(familyquery).fetchall()


    return render_template(
        "viewallcocktails.html",  allfamilies=allfamilies, allcocktails=allcocktails, defaults=session["defaults"], form=form
    )

@app.route("/viewuser")
@login_required
def viewuser():

    form = ModifyCocktailForm()

    cocktailquery = text("SELECT name, id, family, build, source, notes, recipe, ingredient_list \
                        FROM cocktails \
                        WHERE user_id = :user_id")
   
    usercocktails = db.session.execute(cocktailquery, {"user_id": current_user.id}).fetchall()
   
    userfamilies = set(Cocktail.family for Cocktail in usercocktails)

    return render_template(
        "viewuser.html", usercocktails=usercocktails, userfamilies=userfamilies, form=form
    )

@app.route("/viewcommon")
def viewcommon():

    commoncocktailsquery = text("""
                                SELECT name, build, source, recipe, family, ingredient_list
                                FROM common_cocktails
                                """)
    commoncocktails = db.session.execute(commoncocktailsquery).fetchall()

    familyquery = text("SELECT DISTINCT family FROM common_cocktails")
    allfamilies = db.session.scalars(familyquery).fetchall()
    
    return render_template(
        "viewcommon.html", commoncocktails=commoncocktails, allfamilies=allfamilies
    )

# NEW Change Recipe Modal from viewallcocktails/viewuser->modify
@app.route("/modifycocktail", methods=["GET", "POST"])
@login_required
def modifycocktail():

    form = ModifyCocktailForm()
    name = form.name.data

    if request.method == "POST":

        if "modify" in request.form:
            cocktailquery = text("SELECT id, name, build, source, family, notes FROM cocktails WHERE name = :name AND user_id = :user_id")
            cocktail = db.session.execute(cocktailquery, {"name": name, "user_id": current_user.id}).fetchone()

            amountsquery = text("SELECT ingredient_id, amount, ingredient_source, sequence FROM amounts WHERE cocktail_id = :cocktail_id ORDER BY sequence ASC")
            amounts = db.session.execute(amountsquery, {"cocktail_id": cocktail.id}).fetchall()

            ingredientsquery = text("""
                                    SELECT ci.id, ci.name FROM common_ingredients ci
                                    LEFT JOIN amounts a ON ci.id = a.ingredient_id
                                    WHERE a.cocktail_id = :cocktail_id AND a.ingredient_source = 'common'
                                    UNION 
                                    SELECT i.id, i.name FROM ingredients i 
                                    LEFT JOIN amounts a ON i.id = a.ingredient_id
                                    WHERE a.user_id = :user_id AND a.cocktail_id = :cocktail_id AND a.ingredient_source = 'user'
                                    """)
            ingredients = db.session.execute(ingredientsquery, {"user_id": current_user.id, "cocktail_id": cocktail.id}).fetchall()

            form.family.choices = [(f, f) for f in db.session.scalars(union((select(CommonCocktail.family.distinct())), (select(Cocktail.family.distinct())))).fetchall()]
            family = cocktail.family
            form.family.data = family
            
            types = db.session.scalars(select(CommonIngredient.type.distinct())).fetchall()

            return render_template(
                "modifycocktail.html", cocktail=cocktail, amounts=amounts, ingredients=ingredients, types=types, form=form
            )
        
        elif "deletebutton" in request.form:
            return render_template(
                "areyousurecocktail.html", name=name, form=form
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
            
            flash('Cocktail Deleted', "danger")
            return redirect(url_for("viewcocktails"))

        elif "cancel" in request.form:
            return redirect(url_for("viewcocktails"))
        
        elif "submitbutton" in request.form:

            # update cocktail in db

             # Get list of amounts
            rawamounts = request.form.getlist('amount')
            amounts = list(filter(None, rawamounts))
            # Get list of ingredients
            rawingredients = request.form.getlist('q')
            ingredients = list(filter(None, rawingredients))
            
            # Check for existing cocktail
            rowsquery = text("SELECT name FROM cocktails WHERE name = :name AND user_id = :user_id")
            rows = db.session.scalar(rowsquery, {"name": form.name.data, "user_id": current_user.id})

            if rows and rows != form.name.data:
                return apology("You already have a cocktail by that name", 403)
            
            else:

                # clear amounts for cocktail
                clearamounts = text("DELETE FROM amounts WHERE cocktail_id = :cocktail_id AND user_id = :user_id")
                db.session.execute(clearamounts, {"cocktail_id": form.id.data, "user_id": current_user.id})
                db.session.commit()

                # for each li...
                for i in range(len(amounts)):
                    # get values for amounts and ingredients
                    dbamount = amounts[i]
                    dbingredient = ingredients[i]
                    # get ingredient source
                    id_sourcequery = text("SELECT 'common' AS source, id FROM common_ingredients \
                        WHERE name = :name \
                        UNION SELECT \
                        'user' AS source, id \
                        FROM ingredients \
                        WHERE name = :name AND user_id = :user_id")
                    id_source = db.session.execute(id_sourcequery, {"name": dbingredient, "user_id": current_user.id}).fetchone()
                    
                    ingredient_source = id_source.source
                    ingredient_id = id_source.id   

                    # write into database
                    insertquery = text("INSERT INTO amounts (cocktail_id, ingredient_id, amount, user_id, ingredient_source, sequence) \
                            VALUES(:cocktail_id, :ingredient_id, :amount, :user_id, :ingredient_source, :sequence)")
                    db.session.execute(insertquery, {"cocktail_id": form.id.data, "ingredient_id": ingredient_id, "amount": dbamount, "user_id": current_user.id, "ingredient_source": ingredient_source, "sequence": (i + 1)})
                    db.session.commit()

                # Generate text for ingredients and ingredient_list
               
                recipequery = text("""
                                   SELECT * FROM (
                                        SELECT i.id, i.name, i.short_name, 'user' AS source, a.sequence
                                        FROM ingredients i
                                        LEFT JOIN amounts a ON i.id = a.ingredient_id
                                        WHERE a.ingredient_source = 'user' AND a.cocktail_id = :cocktail AND a.user_id = :user_id
                                        
                                        UNION
                                        
                                        SELECT ci.id, ci.name, ci.short_name, 'common' AS source, aa.sequence
                                        FROM common_ingredients ci
                                        LEFT JOIN amounts aa ON ci.id = aa.ingredient_id
                                        WHERE aa.ingredient_source = 'common' AND aa.cocktail_id = :cocktail AND aa.user_id = :user_id
                                    ) AS combined_ingredients
                                    ORDER BY sequence ASC; 
                                   """)
                reciperesults = db.session.execute(recipequery, {"user_id": current_user.id, "cocktail": form.id.data}).fetchall()
                amountsq = text("""
                                SELECT ingredient_id, amount, cocktail_id, sequence
                                FROM amounts
                                WHERE cocktail_id = :cocktail AND user_id = :user_id
                                ORDER BY sequence ASC
                                """)
                amountresults = db.session.execute(amountsq, {"cocktail": form.id.data, "user_id": current_user.id}).fetchall()

                recipe = ""
                for amount, ingredient in zip(amountresults, reciperesults):
                    recipe += f"{amount.amount} {ingredient.name}\n"
                
                ingredient_list = ', '.join([row.short_name if row.short_name else row.name for row in reciperesults])
                
                # Update cocktail in db
                db.session.execute(
                    update(Cocktail).where(Cocktail.id == form.id.data)
                    .where(Cocktail.user_id == current_user.id)
                    .values(name=form.name.data, 
                            build=form.build.data, 
                            source=form.source.data, 
                            family=form.family.data, 
                            notes=form.notes.data, 
                            recipe=recipe, 
                            ingredient_list=ingredient_list))
                db.session.commit()

                

                return redirect(url_for("viewcocktails"))        
        

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

    cocktailsquery = text("""
                        SELECT cc.id, cc.name, cc.family, cc.build, cc.source, cc.recipe, cc.ingredient_list, NULL AS notes, 'common' AS source 
                        FROM common_cocktails cc 
                        JOIN common_amounts ca ON cc.id = ca.cocktail_id 
                        LEFT JOIN common_ingredients ci ON ca.ingredient_id = ci.id 
                        LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id 
                        WHERE (cs.stock != 1 AND cs.user_id = :user_id) 
                        GROUP BY cc.id 
                        HAVING COUNT(*) = 1 
                        UNION 
                        SELECT c.id, c.name, c.family, c.build, c.source, c.recipe, c.ingredient_list, c.notes, 'user' AS source 
                        FROM cocktails c 
                        JOIN amounts a ON c.id = a.cocktail_id 
                        LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' 
                        LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' 
                        WHERE (
                          (a.ingredient_source = 'user' AND i.stock != 1 AND i.user_id = :user_id) 
                        OR 
                          (a.ingredient_source = 'common' AND cs.stock != 1 AND cs.user_id = :user_id) 
                          )
                        GROUP BY c.id 
                        HAVING COUNT(*) = 1
                          """) 
    cocktails = db.session.execute(cocktailsquery, {"user_id": current_user.id}).fetchall()

    missingquery = text("""WITH sad_cocktails AS (
                            SELECT cc.name 
                            FROM common_cocktails cc 
                            JOIN common_amounts ca ON cc.id = ca.cocktail_id 
                            LEFT JOIN common_ingredients ci ON ca.ingredient_id = ci.id 
                            LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id 
                            WHERE 
                                (cs.stock != 1 AND cs.user_id = :user_id) 
                            GROUP BY cc.name 
                            HAVING COUNT(*) = 1 
                            UNION 
                            SELECT c.name 
                            FROM cocktails c 
                            JOIN amounts a ON c.id = a.cocktail_id 
                            LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' 
                            LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' 
                            WHERE (
                                (a.ingredient_source = 'user' AND i.stock != 1 AND i.user_id = :user_id AND c.user_id = :user_id) 
                            OR 
                                (a.ingredient_source = 'common' AND cs.stock != 1 AND cs.user_id = :user_id AND c.user_id = :user_id) 
                                )
                            GROUP BY c.name 
                            HAVING COUNT(*) = 1 
                        ), 
                        sad_ingredients AS (
                            SELECT a.ingredient_id, a.ingredient_source FROM amounts a
                            LEFT JOIN cocktails c ON c.id = a.cocktail_id 
                            WHERE (c.name IN (SELECT name FROM sad_cocktails) AND a.user_id = :user_id) 
                            UNION
                            SELECT ca.ingredient_id, ca.ingredient_source FROM common_amounts ca
                            LEFT JOIN common_cocktails coco ON coco.id = ca.cocktail_id
                            WHERE coco.name IN (SELECT name FROM sad_cocktails)
                        )
                        SELECT id, name FROM ingredients WHERE (id IN (SELECT ingredient_id FROM sad_ingredients) AND stock != 1) 
                        UNION 
                        SELECT ci.id, ci.name FROM common_ingredients ci 
                        JOIN common_stock cs ON ci.id = cs.ingredient_id 
                        WHERE (cs.stock != 1 AND cs.user_id = :user_id AND ci.id IN (SELECT ingredient_id FROM sad_ingredients)) 
                        GROUP BY ci.id
                          """)
    missing_ingredients = db.session.execute(missingquery, {"user_id": current_user.id}).fetchall()
   
    ingredientsquery = text("SELECT id, name, short_name FROM common_ingredients UNION SELECT id, name, short_name FROM ingredients WHERE user_id = :user_id")
    ingredients = db.session.execute(ingredientsquery, {"user_id": current_user.id}).fetchall()
   
    amountsquery = text("SELECT cocktail_id, ingredient_id, amount, 'common' AS source FROM common_amounts UNION SELECT cocktail_id, ingredient_id, amount, 'user' AS source FROM amounts WHERE user_id = :user_id")
    amounts = db.session.execute(amountsquery, {"user_id": current_user.id}).fetchall()

    return render_template(
        "missingoneall.html", cocktails=cocktails, ingredients=ingredients, amounts=amounts, missing_ingredients=missing_ingredients, defaults=session["defaults"]
    )

@app.route("/missingoneuser")
@login_required
def missingoneuser():

    cocktailquery = text("SELECT c.name, c.id, c.family, c.build, c.source, c.notes, c.recipe, c.ingredient_list "
                        "FROM cocktails c "
                        "JOIN amounts a ON c.id = a.cocktail_id "
                        "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
                        "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
                        "WHERE (\
                            (a.ingredient_source = 'user' AND i.stock != 1 AND i.user_id = :user_id AND c.user_id = :user_id) "
                            "OR \
                            (a.ingredient_source = 'common' AND cs.stock != 1 AND cs.user_id = :user_id AND c.user_id = :user_id) "
                            ") \
                        GROUP BY c.id "
                        "HAVING COUNT(*) = 1")
    
    cocktails = db.session.execute(cocktailquery, {"user_id": current_user.id}).fetchall()

    missingquery = text("""
                            WITH sad_cocktails AS (
                            SELECT c.name 
                            FROM cocktails c 
                            JOIN amounts a ON c.id = a.cocktail_id 
                            LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' 
                            LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' 
                            WHERE (
                                (a.ingredient_source = 'user' AND i.stock != 1 AND i.user_id = :user_id AND c.user_id = :user_id) 
                                OR 
                                (a.ingredient_source = 'common' AND cs.stock != 1 AND cs.user_id = :user_id AND c.user_id = :user_id) 
                                ) 
                            GROUP BY c.name 
                            HAVING COUNT(*) = 1
                        ),
                        sad_ingredients AS (
                            SELECT a.ingredient_id, a.ingredient_source 
                            FROM amounts a
                            LEFT JOIN cocktails c ON c.id = a.cocktail_id 
                            WHERE (c.name IN (SELECT name FROM sad_cocktails) AND a.user_id = :user_id)
                        )
                        SELECT id, name FROM ingredients WHERE (id IN (SELECT ingredient_id FROM sad_ingredients) AND stock != 1) 
                        UNION 
                        SELECT ci.id, ci.name FROM common_ingredients ci 
                        JOIN common_stock cs ON ci.id = cs.ingredient_id 
                        WHERE (cs.stock != 1 AND cs.user_id = :user_id AND ci.id IN (SELECT ingredient_id FROM sad_ingredients)) 
                        GROUP BY ci.id
                        """)
    
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

    cocktailsquery = text("SELECT c.name, c.id, c.family, c.build, c.source, c.notes, c.recipe, c.ingredient_list "
        "FROM cocktails c "
        "JOIN amounts a ON c.id = a.cocktail_id "
        "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
        "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
        "WHERE (a.ingredient_source = 'user' AND i.stock = 1 AND i.user_id = :user_id AND c.user_id = :user_id) "
        "OR (a.ingredient_source = 'common' AND cs.stock = 1 AND cs.user_id = :user_id AND c.user_id = :user_id) "
        "GROUP BY c.id "
        "HAVING COUNT(*) = (SELECT COUNT(*) FROM amounts a3 WHERE a3.cocktail_id = c.id)")
    cocktails = db.session.execute(cocktailsquery, {"user_id": current_user.id}).fetchall()

    families = set(Cocktail.family for Cocktail in cocktails)

    return render_template(
        "whatstodrinkuser.html", cocktails=cocktails, families=families
    )


@app.route("/whatstodrinkall")
def whatstodrinkall():

    cocktailquery = text( "SELECT cc.name, cc.id, cc.family, cc.build, cc.source, cc.recipe, cc.ingredient_list, NULL AS notes "
    "FROM common_cocktails cc "
    "JOIN common_amounts ca ON cc.id = ca.cocktail_id "
    "LEFT JOIN common_ingredients ci ON ca.ingredient_id = ci.id "
    "LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id "
    "WHERE (cs.stock = 1 AND cs.user_id = :user_id) "
    "GROUP BY cc.id "
    "HAVING COUNT(*) = (SELECT COUNT(*) FROM common_amounts a2 WHERE a2.cocktail_id = cc.id) "
    "UNION "
    "SELECT c.name, c.id, c.family, c.build, c.source, c.recipe, c.ingredient_list, c.notes "
    "FROM cocktails c "
    "JOIN amounts a ON c.id = a.cocktail_id "
    "LEFT JOIN ingredients i ON a.ingredient_id = i.id AND a.ingredient_source = 'user' "
    "LEFT JOIN common_stock cs ON a.ingredient_id = cs.ingredient_id AND a.ingredient_source = 'common' "
    "WHERE (a.ingredient_source = 'user' AND i.stock = 1 AND i.user_id = :user_id AND c.user_id = :user_id) "
    "OR (a.ingredient_source = 'common' AND cs.stock = 1 AND cs.user_id = :user_id AND c.user_id = :user_id) "
    "GROUP BY c.id "
    "HAVING COUNT(*) = (SELECT COUNT(*) FROM amounts a3 WHERE a3.cocktail_id = c.id)")
    cocktails = db.session.execute(cocktailquery, {"user_id": current_user.id}).fetchall()

    families = set(Cocktail.family for Cocktail in cocktails)

    return render_template(
        "whatstodrinkall.html", cocktails=cocktails, families=families
        )

