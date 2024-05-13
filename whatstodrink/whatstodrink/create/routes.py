from flask import flash, redirect, render_template, request, url_for, Blueprint
from whatstodrink.__init__ import db
from sqlalchemy import select, text, update, exc, or_
from whatstodrink.models import Cocktail, Ingredient, Stock, Amount
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
                short_name=form.short_name.data,
                notes=form.notes.data,
                shared=0
            )
            
            db.session.add(new_ingredient)
            try:
                db.session.commit()
            except exc.SQLAlchemyError as e:
                db.session.rollback()
                print("Transaction rolled back due to error:", e)
            
            new_stock = Stock(
                stock=form.stock.data,
                user_id=current_user.id,
                ingredient_id=new_ingredient.id
            )
            db.session.add(new_stock)
            try:
                db.session.commit()
                flash("{}} Added".format(new_ingredient.name), "primary")
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
            new_ingredient = Ingredient(
                user_id=current_user.id,
                name=form.name.data,
                type=form.type.data,
                short_name=form.short_name.data,
                notes=form.notes.data,
                shared=0
            )            
            db.session.add(new_ingredient)
            try:
                db.session.commit()
            except exc.SQLAlchemyError as e:
                db.session.rollback()
                print("Transaction rolled back due to error:", e)
            # Add new stock entry 
            new_stock = Stock(
                stock=form.stock.data,
                user_id=current_user.id,
                ingredient_id=new_ingredient.id
            )
            db.session.add(new_stock)
            try:
                db.session.commit()
                flash("{}} Added".format(new_ingredient.name), "primary")
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
            rawamounts = [amount.strip() for amount in request.form.getlist('amount')]
            
            amounts = list(filter(None, rawamounts))
            # Get list of ingredients
            rawingredients = request.form.getlist('q')
            ingredients = list(filter(None, rawingredients))
               
            recipe = ""
            for amount, ingredient in zip(amounts, ingredients):
                # concatenate amount/ingredient with unit separator delimiter, and newline
                recipe += f"{amount}{chr(31)}{ingredient}\n"
            
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
          
            # Add amounts to db
            # initialize names list and sequence counter
            list_names = []
            counter = 1

            for amount, ingredient in zip(amounts, ingredients):
                info = db.session.execute(
                    select(Ingredient.id, Ingredient.short_name, Ingredient.name)
                    .where(Ingredient.name == ingredient)
                    .where(or_(Ingredient.user_id == current_user.id, Ingredient.shared == 1))
                    ).first()
                new_amount = Amount(cocktail_id=newcocktail.id,
                                    ingredient_id=info.id,
                                    amount=amount,
                                    sequence=counter,
                                    user_id=current_user.id)
                db.session.add(new_amount)
                # Get short name and add to names list
                name = info.short_name if info.short_name else info.name
                if name not in list_names:
                    list_names.append(name)
                counter += 1

             # generate ingredientlist
            
            ingredient_list = ', '.join(list_names)
            
            db.session.execute(
                update(Cocktail).where(Cocktail.id == newcocktail.id)
                .where(Cocktail.user_id == current_user.id)
                .values(ingredient_list=ingredient_list)
            )
            try:
                db.session.commit()
                flash("{}} Added".format(newcocktail.name), "primary")

            except exc.SQLAlchemyError as e:
                db.session.rollback()
                print("Transaction rolled back due to error:", e)
        
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
                short_name=form.short_name.data,
                notes=form.notes.data,
                shared=0
            )
            db.session.add(new_ingredient)
            try:
                db.session.commit()
            except exc.SQLAlchemyError as e:
                db.session.rollback()
                print("Transaction rolled back due to error:", e)

            # Add new stock entry 
            new_stock = Stock(
                stock=form.stock.data,
                user_id=current_user.id,
                ingredient_id=new_ingredient.id
            )
            db.session.add(new_stock)
            try:
                db.session.commit()
            except exc.SQLAlchemyError as e:
                db.session.rollback()
                print("Transaction rolled back due to error:", e)
            return form.name.data
        # if not validated
        else:
            # Query database for ingredient
            rows = db.session.execute(select(Ingredient.name)
                                      .where(Ingredient.name == form.name.data)
                                      .where(or_(Ingredient.user_id == current_user.id, Ingredient.shared == 1))
            ).first()
            # if it already exists, return the name of the ingredient
            if rows:
                return rows.name
            # if it doesn't, return the "ignore" keyword
            else:
                return "ignore"