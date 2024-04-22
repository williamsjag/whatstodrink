from flask import flash, redirect, render_template, request, url_for, Blueprint
from whatstodrink.__init__ import db
from sqlalchemy import select, text, update, exc
from whatstodrink.models import Cocktail, Ingredient
from whatstodrink.create.forms import AddIngredientForm, AddCocktailForm
from flask_login import current_user, login_required

create = Blueprint('create', __name__)

# Add ingredient modal from Manage Ingredients
@create.route("/addingredientmodal2", methods=["GET", "POST"])
@login_required
def addingredientmodal2():
     
    form = AddIngredientForm()

    # reached via post
    if request.method == "POST":
        
        if form.validate_on_submit():
    
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
            try:
                db.session.commit()
                flash("Ingredient Added", "primary")
            except exc.SQLAlchemyError as e:
                db.session.rollback()
                print("Transaction rolled back due to error:", e)
        
                
            return redirect(url_for("modify.manageingredients"))
        else:
            return render_template("addingredienterrors.html", form=form)
        
        # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template(
            "addingredientmodal2.html", form=form
        )


# AddIngredient/AddCocktail/Amounts and related routes


@create.route("/addingredient", methods=["GET", "POST"])
@login_required
def addingredient():

    form = AddIngredientForm()

    # reached via post
    if request.method == "POST":
        if form.validate_on_submit():
            if "cancelbutton" in request.form:
                return redirect(url_for("modify.manageingredients"))
            # insert new ingredient into db
            newingredient = Ingredient(name=form.name.data, short_name=form.short_name.data, type=form.type.data, notes=form.notes.data, stock=form.stock.data, user_id=current_user.id)
            db.session.add(newingredient)
            try:
                db.session.commit()
                flash('Ingredient Added', 'primary')
            except exc.SQLAlchemyError as e:
                db.session.rollback()
                print("Transaction rolled back due to error:", e)
          
            
            return redirect(url_for(
                "create.addingredient"
            ))
        else:
            if "cancelbutton" in request.form:
                return redirect(url_for("modify.manageingredients"))
            return render_template('addingredient.html', form=form)
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template(
            "addingredient.html", form=form
        )
    

@create.route("/addcocktail", methods=["GET", "POST"])
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
            try:
                db.session.commit()
            except exc.SQLAlchemyError as e:
                db.session.rollback()
                print("Transaction rolled back due to error:", e)
          

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
                try:
                    db.session.commit()
                    counter += 1
                except exc.SQLAlchemyError as e:
                    db.session.rollback()
                    print("Transaction rolled back due to error:", e)
           

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
            try:
                db.session.commit()
            except exc.SQLAlchemyError as e:
                db.session.rollback()
                print("Transaction rolled back due to error:", e)
        
       

            flash("Cocktail Added", 'primary')
            return redirect(url_for(
                "create.addcocktail"
            ))
        
        else:
            return render_template(
                "addcocktail.html", form=form
            )
    
# Create New Ingredient modal from Add Cocktail
@create.route("/addingredientmodal", methods=["GET", "POST"])
@login_required
def addingredientmodal():

    form = AddIngredientForm()

    if request.method == "GET":
        return render_template("addingredientmodal.html", form=form)
    # If POST
    else:
        # Ensure ingredient was submitted
        if form.validate_on_submit():
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
            try:
                db.session.commit()
            except exc.SQLAlchemyError as e:
                db.session.rollback()
                print("Transaction rolled back due to error:", e)
          
            return form.name.data
        # if not validated
        else:
            # Query database for ingredient
            rowsquery = text("""SELECT name FROM ingredients WHERE name = :ingredientname AND user_id = :user_id
                             UNION
                             SELECT name FROM common_ingredients WHERE name = :ingredientname""")
            rows = db.session.execute(rowsquery, {"ingredientname": form.name.data, "user_id": current_user.id}).fetchall()

            # if it already exists, return the name of the ingredient
            if rows:
                return form.name.data
            # if it doesn't, return the "ignore" keyword
            else:
                return "ignore"