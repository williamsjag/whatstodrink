from flask import flash, redirect, render_template, request, url_for, Blueprint, session
from whatstodrink.__init__ import db
from sqlalchemy import select, union, text, update, exc, or_, delete, outerjoin, func
from sqlalchemy.orm import outerjoin
from whatstodrink.models import Cocktail, Ingredient, Stock, Amount
from whatstodrink.modify.forms import ManageIngredientsForm, ModifyIngredientForm, DeleteForm, ModifyCocktailForm
from whatstodrink.view.forms import ViewIngredientForm
from flask_login import current_user, login_required

modify = Blueprint('modify', __name__)

@modify.route("/manageingredients", methods=["GET", "POST"])
@login_required
def manageingredients():

    form = ManageIngredientsForm()
    
    if request.method =="GET":

        # check for search queries 
        q = request.args.get('q')
      
        # if filter bar is entered
        if q is not None:
            # Get Types included in search for headers
            query = (
                select(Ingredient.type.distinct())
                .select_from(Ingredient)
                .outerjoin(Stock, (Ingredient.id == Stock.ingredient_id) & (Stock.user_id == current_user.id))
                .where(func.lower(Ingredient.name).like('%' + q + '%'))
            )

            types = db.session.scalars(query).all()

            # Get ingredients that match
            ingredientsquery = (select(Ingredient.id, Ingredient.name, Ingredient.type, Ingredient.short_name, Ingredient.notes, Stock.stock, Ingredient.shared)
                                .join(Ingredient.stock)
                                .where(or_(Ingredient.user_id == current_user.id, Ingredient.shared == 1))
                                .where(func.lower(Ingredient.name).like('%' + q + '%'))
            )
            
            ingredients = db.session.execute(ingredientsquery).fetchall()

            if request.headers.get('HX-Trigger') == 'search':
                return render_template("/ingredientstable.html", ingredients=ingredients, types=types, form=form)
            else:
                return render_template("/manageingredients.html", ingredients=ingredients, types=types, form=form)
            
        # no search bar, normal page load
        else:
            typesquery = (select(Ingredient.type.distinct())
                                .where(or_(Ingredient.user_id == current_user.id, Ingredient.shared == 1)))
            types = db.session.scalars(typesquery).fetchall()
            ingredientsquery = (select(Ingredient.shared, Ingredient.id, Ingredient.name, Ingredient.type, Ingredient.short_name, Ingredient.notes, Stock.stock)
                                .join(Ingredient.stock)
                                .where(or_(Ingredient.user_id == current_user.id, Ingredient.shared == 1))
                                )
            ingredients = db.session.execute(ingredientsquery).fetchall()

            return render_template(
                "manageingredients.html", ingredients=ingredients, types=types, form=form
            )
    elif request.method =="POST":
        for key, value, in request.form.items():
            if key.startswith('stock_'):
                ingredient_name = key.replace('stock_', '')
                ingredient_id = request.form.get(f'id_{ingredient_name}')
                ingredient_stock = value
            elif key.startswith('id_'):
                ingredient_name = key.replace('id_', '')
                ingredient_id = value
                ingredient_stock = request.form.get(f'stock_{ingredient_name}')

                # set stock for ingredients
                stock = 1 if ingredient_stock == 'on' else 0
                sql_query = (update(Stock)
                             .where(Stock.ingredient_id == ingredient_id)
                             .where(Stock.user_id == current_user.id)
                             .values(stock=stock))
                # Update the stock value
                db.session.execute(sql_query)
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                
            
        return redirect(url_for(
            "modify.manageingredients", form=form
        ))
    

# Modify Ingredient modal from ManageIngredients -> viewingredientmodal
@modify.route("/modify_ingredient", methods=["GET", "POST"])
@login_required
def modify_ingredient():

    form = ViewIngredientForm()
    ingredient = form.name.data
    
    if request.method == "POST":
            
        if "submitbutton" in request.form:

            form = ModifyIngredientForm()

            if form.validate_on_submit():
            
                id = form.id.data
                newtype = form.type.data
                newnotes = form.notes.data
                newname = form.name.data
                shortname = form.short_name.data
                updatequery = text("UPDATE ingredients SET type = :type, notes = :notes, name = :name, short_name = :short_name WHERE id = :id AND user_id = :user_id")
                db.session.execute(updatequery,  {"id": id, "type": newtype, "notes": newnotes, "name": newname, "short_name": shortname, "user_id": current_user.id})
                try:
                    db.session.commit()
                except exc.SQLAlchemyError as e:
                    db.session.rollback()
                    print("Transaction rolled back due to error:", e)
               
                # Check for cocktails using this ingredient
                cocktails = db.session.scalars(select(Amount.cocktail_id).where(Amount.ingredient_id == id)).fetchall()

                for cocktail in cocktails:
                    ingredientsq = text("""
                                    SELECT * FROM (
                                            SELECT i.id, i.name, i.short_name, a.sequence
                                            FROM ingredients i
                                            LEFT JOIN amounts a ON i.id = a.ingredient_id
                                            WHERE a.cocktail_id = :cocktail AND a.user_id = :user_id
                                            ) AS subquery
                                        ORDER BY sequence ASC;
                                        """)
                    ingredients = db.session.execute(ingredientsq, {"user_id": current_user.id, "cocktail": cocktail}).fetchall()
                   
                    amounts = db.session.execute(select(Amount.ingredient_id, Amount.cocktail_id, Amount.amount, Amount.sequence)
                                                 .where(Amount.cocktail_id == cocktail)
                                                 .where(Amount.user_id == current_user.id)
                                                 .order_by(Amount.sequence)
                    ).fetchall()

                    recipe = ""
                    for amount, ingredient in zip(amounts, ingredients):
                        recipe += f"{amount.amount} {ingredient.name}\n"
                    
                    ingredient_list = ', '.join([row.short_name if row.short_name else row.name for row in ingredients])
                    db.session.execute(
                        update(Cocktail).where(Cocktail.id == cocktail)
                        .where(Cocktail.user_id == current_user.id)
                        .values(recipe=recipe, 
                                ingredient_list=ingredient_list))
                    try:
                        db.session.commit()
                    except exc.SQLAlchemyError as e:
                        db.session.rollback()
                        print("Transaction rolled back due to error:", e)

                flash("Ingredient Modified", "primary")
                return redirect(url_for('modify.manageingredients'))
            # If form not valid
            else:
                ingredient_id = form.id.data
                ingredient = db.session.execute(select(Ingredient).where(Ingredient.id == ingredient_id).where(Ingredient.user_id == current_user.id)).fetchone()
                ingredient = ingredient[0]
                types = db.session.scalars(select(Ingredient.type.distinct())).fetchall()
                return render_template ("modifyingredientformerrors.html", form=form, types=types, ingredient=ingredient)

        elif "deletebutton" in request.form:

            form = DeleteForm()

            ingredientId = db.session.scalar(select(Ingredient.id).where(Ingredient.name == ingredient).where(Ingredient.user_id == current_user.id))

            cocktails = db.session.scalars(select(Amount.cocktail_id).where(Amount.ingredient_id == ingredientId)).fetchall()

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
            ingredient = db.session.execute(select(Ingredient.id, Ingredient.name, Ingredient.type, Ingredient.short_name, Ingredient.notes)
                                            .where(Ingredient.name == name)
                                            .where(Ingredient.user_id == current_user.id)).fetchall()

            types = db.session.scalars(select(Ingredient.type.distinct())).fetchall()

            form = ModifyIngredientForm()

            if ingredient:

                return render_template("modifyingredient.html", ingredient=ingredient[0], types=types, form=form)
        
        elif "deleteconfirmed" in request.form:

            form = DeleteForm()

            ingredient_delete = form.id.data
            db.session.execute(delete(Stock)
                               .where(Stock.ingredient_id == ingredient_delete)
                               .where(Stock.user_id == current_user.id))
            db.session.execute(delete(Ingredient)
                               .where(Ingredient.id == ingredient_delete)
                               .where(Ingredient.user_id == current_user.id))
            try:
                db.session.commit()
                flash("Ingredient Deleted", "warning")
            except exc.SQLAlchemyError as e:
                db.session.rollback()
                print("Transaction rolled back due to error:", e)
            
            return redirect(url_for("modify.manageingredients"))
        
        elif "close" in request.form:

            return redirect(url_for("modify.manageingredients"))
        
@modify.route("/modifycocktail", methods=["GET", "POST"])
@login_required
def modifycocktail():

    form = ModifyCocktailForm()
    name = form.name.data

    if request.method == "POST":

        if "modify" in request.form:
            cocktail = db.session.execute(select(Cocktail.id, Cocktail.name, Cocktail.build, Cocktail.source, Cocktail.family, Cocktail.notes)
                                          .where(Cocktail.name == name)
                                          .where(Cocktail.user_id == current_user.id)).fetchone()
            amounts = db.session.execute(select(Amount.ingredient_id, Amount.amount, Amount.sequence)
                                         .where(Amount.cocktail_id == cocktail.id)
                                         .order_by(Amount.sequence.asc())).fetchall()
            ingredientsquery = text("""
                                    SELECT id, name FROM ingredients
                                    LEFT JOIN amounts a ON ingredients.id = a.ingredient_id
                                    WHERE a.user_id = :user_id AND a.cocktail_id = :cocktail_id
                                    """)
            ingredients = db.session.execute(ingredientsquery, {"user_id": current_user.id, "cocktail_id": cocktail.id}).fetchall()

    
            family = cocktail.family
            form.family.data = family
            
            types = db.session.scalars(select(Ingredient.type.distinct())).fetchall()

            return render_template(
                "modifycocktail.html", cocktail=cocktail, amounts=amounts, ingredients=ingredients, types=types, form=form, view=session["view"]
            )
        
        elif "deletebutton" in request.form:

            id = form.id.data
            name = db.session.scalar(select(Cocktail.name).where(Cocktail.id == id).where(Cocktail.user_id == current_user.id))
            return render_template(
                "areyousurecocktail.html", name=name, form=form
            )
        
        elif "deleteconfirmed" in request.form:
            cocktail_delete = request.form.get("cocktail_delete")
            amountsdeletequery = text("WITH CocktailToDelete AS \
                       (SELECT id FROM cocktails WHERE name = :name AND user_id = :user_id LIMIT 1) \
                       DELETE FROM amounts \
                       WHERE cocktail_id IN (SELECT id FROM CocktailToDelete)")
            cocktaildeletequery = text("DELETE FROM cocktails WHERE name = :name AND user_id = :user_id")
            db.session.execute(amountsdeletequery, {"name": cocktail_delete, "user_id": current_user.id})
            db.session.execute(cocktaildeletequery, {"name": cocktail_delete, "user_id": current_user.id})
            try:
                db.session.commit()
                flash('Cocktail Deleted', "warning")
            except exc.SQLAlchemyError as e:
                db.session.rollback()
                print("Transaction rolled back due to error:", e)

            return redirect(url_for("view.viewcocktails"))

        elif "cancel" in request.form:
            return redirect(url_for("view.viewcocktails"))
        
        elif "submitbutton" in request.form:

            if form.validate_on_submit():

                # update cocktail in db

                # Get list of amounts
                rawamounts = [amount.strip() for amount in request.form.getlist('amount')]
                amounts = list(filter(None, rawamounts))
                # Get list of ingredients
                rawingredients = request.form.getlist('q')
                ingredients = list(filter(None, rawingredients))
                
                # Check for existing cocktail
                namequery = text("SELECT name FROM cocktails WHERE name = :name AND user_id = :user_id")
                rows = db.session.scalar(namequery, {"name": form.name.data, "user_id": current_user.id})

                if rows and rows != form.name.data:
                    return 403
                
                else:

                    # clear amounts for cocktail
                    clearamounts = text("DELETE FROM amounts WHERE cocktail_id = :cocktail_id AND user_id = :user_id")
                    
                    db.session.execute(clearamounts, {"cocktail_id": form.id.data, "user_id": current_user.id})
                    try:
                        db.session.commit()
                    except exc.SQLAlchemyError as e:
                        db.session.rollback()
                        print("Transaction rolled back due to error:", e)
                 
                    # for each li...
                    recipe = ""
                    list_names = []
                    counter = 1
                    for amount, ingredient in zip(amounts, ingredients):
                        info = db.session.execute(
                            select(Ingredient.id, Ingredient.short_name, Ingredient.name)
                            .where(Ingredient.name == ingredient)
                            .where(or_(Ingredient.user_id == current_user.id, Ingredient.shared == 1))
                            ).first()
                        new_amount = Amount(cocktail_id=form.id.data,
                                            ingredient_id=info.id,
                                            amount=amount,
                                            sequence=counter,
                                            user_id=current_user.id)
                        db.session.add(new_amount)
                        # Get short name and add to names list
                        name = info.short_name if info.short_name else info.name
                        if name not in list_names:
                            list_names.append(name)
                        recipe += f"{amount} {ingredient}\n"
                        counter += 1

                    # generate ingredientlist
                    ingredient_list = ', '.join(list_names)
                    
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
                    try:
                        db.session.commit()
                        flash("Cocktail modified!", "primary")
                    except exc.SQLAlchemyError as e:
                        db.session.rollback()
                        print("Transaction rolled back due to error:", e)

                    referrerpath = request.form.get("referrer")
                    referrer = referrerpath[1:]
                    return redirect(url_for("view." + referrer))
                
            # If form not validated   
            else:
                
                cocktail = db.session.execute(select(Cocktail).where(Cocktail.id == form.id.data).where(Cocktail.user_id == current_user.id)).fetchone()[0]

                # Get list of amounts
                rawamounts = [amount.strip() for amount in request.form.getlist('amount')]
                amounts = list(filter(None, rawamounts))
                # Get list of ingredients
                rawingredients = request.form.getlist('q')
                ingredients = list(filter(None, rawingredients))
                for amount, ingredient in zip(amounts, ingredients):
                        ingredient = db.session.scalar(
                            select(Ingredient.name)
                            .where(Ingredient.name == ingredient)
                            .where(or_(Ingredient.user_id == current_user.id, Ingredient.shared == 1))
                            )
                family = cocktail.family
                zipped_a_i = zip(amounts, ingredients)

                return render_template("modifycocktailformerrors.html", form=form, cocktail=cocktail, family=family, zipped_a_i=zipped_a_i)    
        