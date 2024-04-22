from flask import flash, redirect, render_template, request, url_for, Blueprint
from whatstodrink.__init__ import db
from sqlalchemy import select, union, text, update
from whatstodrink.models import Cocktail, Ingredient, CommonCocktail, CommonIngredient, CommonStock
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
                return redirect(url_for('modify.manageingredients'))
            
            else:
                ingredient_id = form.id.data
                ingredient = db.session.execute(select(Ingredient).where(Ingredient.id == ingredient_id).where(Ingredient.user_id == current_user.id)).fetchone()
                ingredient = ingredient[0]
                typesquery = text("SELECT DISTINCT type FROM common_ingredients")
                types = db.session.execute(typesquery).fetchall()
                return render_template ("modifyingredientformerrors.html", form=form, types=types, ingredient=ingredient)

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
        
        elif "deleteconfirmed" in request.form:

            form = DeleteForm()

            ingredient_delete = form.id.data

            deletequery = text("DELETE FROM ingredients WHERE id = :id AND user_id = :user_id")
            db.session.execute(deletequery, {"id": ingredient_delete, "user_id": current_user.id})
            db.session.commit()

            flash("Ingredient Deleted", "warning")
            return redirect(url_for("modify.manageingredients"))
        
        # elif "cancel" in request.form:

        #     return redirect(url_for("manageingredients"))
        
        elif "close" in request.form:

            return redirect(url_for("modify.manageingredients"))
        
@modify.route("/modifycocktail", methods=["GET", "POST"])
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

    
            family = cocktail.family
            form.family.data = family
            
            types = db.session.scalars(select(CommonIngredient.type.distinct())).fetchall()

            return render_template(
                "modifycocktail.html", cocktail=cocktail, amounts=amounts, ingredients=ingredients, types=types, form=form
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
            db.session.execute(amountsdeletequery, {"name": cocktail_delete, "user_id": current_user.id})
            cocktaildeletequery = text("DELETE FROM cocktails WHERE name = :name AND user_id = :user_id")
            db.session.execute(cocktaildeletequery, {"name": cocktail_delete, "user_id": current_user.id})
            db.session.commit()
            
            flash('Cocktail Deleted', "warning")
            return redirect(url_for("view.viewcocktails"))

        elif "cancel" in request.form:
            return redirect(url_for("view.viewcocktails"))
        
        elif "submitbutton" in request.form:

            if form.validate_on_submit():

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
                    return 403
                
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

                    
                    flash("Cocktail modified", "primary")
                    return redirect(url_for("view.viewcocktails"))    
            else:
                
                cocktail = db.session.execute(select(Cocktail).where(Cocktail.id == form.id.data).where(Cocktail.user_id == current_user.id)).fetchone()[0]

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

                family = cocktail.family


                return render_template("modifycocktailformerrors.html", form=form, cocktail=cocktail, ingredients=ingredients, family=family, amounts=amounts)    
        