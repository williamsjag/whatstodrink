from flask import render_template, request, session, Blueprint
from whatstodrink.__init__ import db
from sqlalchemy import select, text, or_, func, and_
from sqlalchemy.orm import joinedload, selectinload
from whatstodrink.models import Ingredient, Cocktail, Amount, Stock
from whatstodrink.view.forms import ViewIngredientForm
from whatstodrink.modify.forms import ModifyCocktailForm
from flask_login import current_user, login_required

view = Blueprint('view', __name__)

# View ingredient modal from ManageIngredients 
@view.route("/viewingredientmodal")
@login_required
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

# Ingredient Search Box from Add Cocktail
@view.route("/ingredientsearch")
@login_required
def ingredientsearch():
    q = request.args.get("q")

    if q:
        results = db.session.execute(select(Ingredient.name)
                                     .where(Ingredient.name.like('%' + q + '%'))
                                     .where(or_(Ingredient.user_id == current_user.id, Ingredient.shared == 1))
                                     .limit(10)
        ).fetchall()        
    else:
        results = []

    return render_template("ingredientsearch.html", results=results)


@view.route("/viewcocktails", methods=["GET", "POST"])
@login_required
def viewcocktails():

    return render_template(
        "viewcocktails.html", defaults=session["defaults"]
    )

@view.route("/viewallcocktails")
@login_required
def viewallcocktails():

    form = ModifyCocktailForm()

    userquery = text("""       
                    SELECT name, id, family, build, source, recipe, ingredient_list, notes, shared \
                    FROM cocktails
                    WHERE (user_id = :user_id OR shared = 1)
                    """)

    cocktails = db.session.execute(userquery, {"user_id": current_user.id}).fetchall()
    
    sorts = db.session.scalars(select(Cocktail.family.distinct())).fetchall()

    return render_template(
        "cocktail_views.html",  sorts=sorts, cocktails=cocktails, form=form
    )

@view.route("/viewuser")
@login_required
def viewuser():

    form = ModifyCocktailForm()

    cocktailquery = text("SELECT name, id, family, build, source, notes, recipe, ingredient_list, shared \
                        FROM cocktails \
                        WHERE user_id = :user_id \
                        ")
   
    cocktails = db.session.execute(cocktailquery, {"user_id": current_user.id}).fetchall()

    if not cocktails:
        return render_template("errors/no_cocktails.html")
   
    sorts = set(Cocktail.family for Cocktail in cocktails)

    return render_template(
        "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form
    )

@view.route("/viewcommon")
@login_required
def viewcommon():
    form = ModifyCocktailForm()
    cocktailsquery = text("""
                                SELECT name, build, source, recipe, family, ingredient_list, shared
                                FROM cocktails
                                WHERE shared = 1
                                """)
    cocktails = db.session.execute(cocktailsquery).fetchall()

    familyquery = text("SELECT DISTINCT family FROM cocktails WHERE shared = 1")
    sorts = db.session.scalars(familyquery).fetchall()
    
    return render_template(
        "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form
    )

@view.route("/missingone")
@login_required
def missingone():
   
    return render_template(
        "missingone.html", defaults=session["defaults"]
    )

@view.route("/missingoneall")
@login_required
def missingoneall():

    cocktailsquery = text("""
                        SELECT c.id, c.name, c.family, c.build, c.source, c.recipe, c.ingredient_list, c.notes, c.shared 
                        FROM cocktails c 
                        JOIN amounts a ON c.id = a.cocktail_id 
                        LEFT JOIN ingredients i ON a.ingredient_id = i.id
                        LEFT JOIN stock s ON a.ingredient_id = s.ingredient_id
                        WHERE (
                          s.stock != 1 AND s.user_id = :user_id AND (c.user_id = :user_id OR c.shared = 1) 
                          )
                        GROUP BY c.id 
                        HAVING COUNT(*) = 1
                          """) 
    cocktails = db.session.execute(cocktailsquery, {"user_id": current_user.id}).fetchall()
    if not cocktails:
        return render_template("errors/no_cocktails.html")

    missingquery = text("""WITH sad_cocktails AS (
                            SELECT c.id 
                            FROM cocktails c 
                            JOIN amounts a ON c.id = a.cocktail_id 
                            LEFT JOIN ingredients i ON a.ingredient_id = i.id
                            LEFT JOIN stock s ON a.ingredient_id = s.ingredient_id
                            WHERE (
                            s.stock != 1 AND s.user_id = :user_id AND (c.user_id = :user_id OR c.shared = 1) 
                            )
                            GROUP BY c.id 
                            HAVING COUNT(*) = 1
                        ), 
                        sad_ingredients AS (
                            SELECT ingredient_id 
                            FROM amounts
                            WHERE (cocktail_id IN (SELECT id FROM sad_cocktails))
                        )
                        SELECT i.id, i.name
                        FROM ingredients i
                        JOIN stock s ON i.id = s.ingredient_id
                        WHERE 
                            (s.stock != 1 AND
                            (s.ingredient_id IN 
                                (
                                SELECT ingredient_id 
                                FROM sad_ingredients 
                                )
                            )
                            ) 
                        GROUP BY i.id
                          """)
    missing_ingredients = db.session.execute(missingquery, {"user_id": current_user.id}).fetchall()

    amountsquery = text("""
                        SELECT a.cocktail_id, a.ingredient_id, a.amount
                        FROM amounts a
                        LEFT JOIN cocktails c ON a.cocktail_id = c.id
                        WHERE a.user_id = :user_id
                        OR c.shared = 1
                        """)
    amounts = db.session.execute(amountsquery, {"user_id": current_user.id}).fetchall()

    
    return render_template(
        "missingone_view.html", cocktails=cocktails, amounts=amounts, missing_ingredients=missing_ingredients, defaults=session["defaults"]
    )

@view.route("/missingoneuser")
@login_required
def missingoneuser():

    # Find cocktails missing one ingredient
    cocktailquery = (
        select(Cocktail)
        .join(Amount, Cocktail.id == Amount.cocktail_id)
        .join(Ingredient, Amount.ingredient_id == Ingredient.id)
        .join(Stock, Ingredient.id == Stock.ingredient_id)
        .where(and_(Stock.stock != 1, Stock.user_id == current_user.id, Cocktail.user_id == current_user.id))
        .group_by(Cocktail.id)
        .having(func.count(Cocktail.id) == 1)
    )
    cocktails = db.session.scalars(cocktailquery).fetchall()
    print(f"{cocktails}")
    missing_ingredients = []
    for cocktail in cocktails:
        # cocktail = cocktail_tuple[0]
        ingredient = db.session.scalars(select(Ingredient, Amount.cocktail_id)
                                         .join(Amount, Ingredient.id == Amount.ingredient_id)
                                         .join(Stock, and_(Ingredient.id == Stock.ingredient_id, Stock.stock != 1))
                                         .where(Amount.cocktail_id == cocktail.id)
                                         ).fetchall()
    missing_ingredients.append(ingredient)
    


    # cocktailquery = text("SELECT c.name, c.id, c.family, c.build, c.source, c.notes, c.recipe, c.ingredient_list "
    #                     "FROM cocktails c "
    #                     "JOIN amounts a ON c.id = a.cocktail_id "
    #                     "LEFT JOIN ingredients i ON a.ingredient_id = i.id "
    #                     "LEFT JOIN stock s ON a.ingredient_id = s.ingredient_id "
    #                     "WHERE (s.stock != 1 AND s.user_id = :user_id AND c.user_id = :user_id) "
    #                     "GROUP BY c.id "
    #                     "HAVING COUNT(*) = 1")
    # cocktails = db.session.execute(cocktailquery, {"user_id": current_user.id}).fetchall()
    # if not cocktails:
    #     return render_template("errors/no_cocktails.html")

    # missingquery = text("""
    #                     WITH sad_cocktails AS (
    #                         SELECT c.id 
    #                         FROM cocktails c 
    #                         JOIN amounts a ON c.id = a.cocktail_id 
    #                         LEFT JOIN ingredients i ON a.ingredient_id = i.id 
    #                         LEFT JOIN stock s ON a.ingredient_id = s.ingredient_id
    #                         WHERE (s.stock != 1 AND s.user_id = :user_id AND c.user_id = :user_id) 
    #                         GROUP BY c.id 
    #                         HAVING COUNT(*) = 1
    #                     ),
    #                     sad_ingredients AS (
    #                         SELECT a.ingredient_id
    #                         FROM amounts a
    #                         LEFT JOIN cocktails c ON c.id = a.cocktail_id 
    #                         WHERE (c.id IN (SELECT id FROM sad_cocktails) AND a.user_id = :user_id)
    #                     )
    #                     SELECT i.id, i.name
    #                     FROM ingredients i
    #                     JOIN stock s on i.id = s.ingredient_id
    #                     WHERE git pu
    #                         (s.stock != 1 AND s.user_id = :user_id AND
    #                         (i.id IN 
    #                             (
    #                             SELECT ingredient_id 
    #                             FROM sad_ingredients 
    #                             ) 
    #                         )
    #                         )
    #                     GROUP BY i.id
    #                     """)
    
    # missing_ingredients = db.session.execute(missingquery, {"user_id": current_user.id}).fetchall()
   
    # amountsquery = text("""
    #                     SELECT cocktail_id, ingredient_id
    #                     FROM amounts 
    #                     WHERE user_id = :user_id
    #                     """)
    # amounts = db.session.execute(amountsquery, {"user_id": current_user.id}).fetchall()

    return render_template(
        "missingone_view.html", cocktails=cocktails, missing_ingredients=missing_ingredients
    )
    

# Whatstodrink and Related Routes 

@view.route("/whatstodrink")
@login_required
def whatstodrink():

    return render_template(
        "whatstodrink.html", defaults=session["defaults"]
    )


@view.route("/whatstodrinkuser")
@login_required
def whatstodrinkuser():

    form = ModifyCocktailForm()
    cocktailsquery = text("""
                        SELECT c.name, c.id, c.family, c.build, c.source, c.notes, c.recipe, c.ingredient_list, c.shared
                        FROM cocktails c
                        JOIN amounts a ON c.id = a.cocktail_id
                        LEFT JOIN ingredients i ON a.ingredient_id = i.id
                        LEFT JOIN stock s ON a.ingredient_id = s.ingredient_id
                        WHERE (
                          s.stock = 1 AND s.user_id = :user_id
                          AND (
                            (i.user_id = :user_id AND c.user_id = :user_id)
                            OR
                            (i.shared = 1 AND c.user_id = :user_id)
                            )
                        )
                        GROUP BY c.id
                        HAVING COUNT(*) = (SELECT COUNT(*) FROM amounts aa WHERE aa.cocktail_id = c.id)
                        """)
    cocktails = db.session.execute(cocktailsquery, {"user_id": current_user.id}).fetchall()

    if not cocktails:
        return render_template("errors/no_cocktails.html")

    sorts = set(Cocktail.family for Cocktail in cocktails)

    return render_template(
        "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form
    )


@view.route("/whatstodrinkall")
@login_required
def whatstodrinkall():

    form = ModifyCocktailForm()
    cocktailsquery = text("""
                        SELECT c.name, c.id, c.family, c.build, c.source, c.notes, c.recipe, c.ingredient_list, c.shared
                        FROM cocktails c
                        JOIN amounts a ON c.id = a.cocktail_id
                        LEFT JOIN ingredients i ON a.ingredient_id = i.id
                        LEFT JOIN stock s ON a.ingredient_id = s.ingredient_id
                        WHERE (
                          s.stock = 1 AND s.user_id = :user_id
                          AND (
                            (i.user_id = :user_id AND (c.user_id = :user_id OR c.shared = 1))
                            OR
                            (i.shared = 1 AND (c.user_id = :user_id OR c.shared = 1))
                            )
                        )
                        GROUP BY c.id
                        HAVING COUNT(*) = (SELECT COUNT(*) FROM amounts aa WHERE aa.cocktail_id = c.id)
                        """)
   
    cocktails = db.session.execute(cocktailsquery, {"user_id": current_user.id}).fetchall()
    if not cocktails:
        return render_template("errors/no_cocktails.html")

    sorts = set(Cocktail.family for Cocktail in cocktails)

    return render_template(
        "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form
        )

