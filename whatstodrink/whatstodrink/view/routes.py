from flask import render_template, request, session, Blueprint
from whatstodrink.__init__ import db
from sqlalchemy import select, text
from whatstodrink.models import Ingredient
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

@view.route("/viewuser")
@login_required
def viewuser():

    form = ModifyCocktailForm()

    cocktailquery = text("SELECT name, id, family, build, source, notes, recipe, ingredient_list \
                        FROM cocktails \
                        WHERE user_id = :user_id")
   
    usercocktails = db.session.execute(cocktailquery, {"user_id": current_user.id}).fetchall()

    if not usercocktails:
        return render_template("errors/no_cocktails.html")
   
    userfamilies = set(Cocktail.family for Cocktail in usercocktails)

    return render_template(
        "viewuser.html", usercocktails=usercocktails, userfamilies=userfamilies, form=form
    )

@view.route("/viewcommon")
@login_required
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
                        SELECT cc.id, cc.name, cc.family, cc.build, cc.source, cc.recipe, cc.ingredient_list, NULL AS notes, 'common' AS source 
                        FROM common_cocktails cc 
                        JOIN common_amounts ca ON cc.id = ca.cocktail_id 
                        LEFT JOIN common_ingredients ci ON ca.ingredient_id = ci.id 
                        LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id 
                        WHERE 
                          (cs.stock != 1 AND cs.user_id = :user_id) 
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
    if not cocktails:
        return render_template("errors/no_cocktails.html")

    missingquery = text("""WITH sad_cocktails AS (
                            SELECT cc.name, 'common' AS source
                            FROM common_cocktails cc 
                            JOIN common_amounts ca ON cc.id = ca.cocktail_id 
                            LEFT JOIN common_ingredients ci ON ca.ingredient_id = ci.id 
                            LEFT JOIN common_stock cs ON ci.id = cs.ingredient_id 
                            WHERE 
                                (cs.stock != 1 AND cs.user_id = :user_id)
                            GROUP BY cc.id
                            HAVING COUNT(*) = 1
                            UNION 
                            SELECT c.name, 'user' AS source
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
                            UNION
                            SELECT ca.ingredient_id, ca.ingredient_source 
                            FROM common_amounts ca
                            LEFT JOIN common_cocktails coco ON coco.id = ca.cocktail_id
                            LEFT JOIN common_stock cs ON ca.ingredient_id = cs.ingredient_id
                            WHERE (coco.name IN (SELECT name FROM sad_cocktails) AND cs.user_id = :user_id)
                        )
                        # Main Query
                        SELECT id, name, 'user' AS source 
                        FROM ingredients 
                        WHERE 
                            (stock != 1 AND
                            (id IN 
                                (
                                SELECT ingredient_id 
                                FROM sad_ingredients 
                                WHERE ingredient_source = 'user'
                                )
                            )
                            ) 
                        
                        UNION 
                         
                        SELECT ci.id, ci.name, 'common' AS source 
                        FROM common_ingredients ci
                        JOIN common_stock cs ON ci.id = cs.ingredient_id 
                        WHERE 
                            (cs.stock != 1 AND cs.user_id = :user_id AND
                            (ci.id IN 
                                (
                                SELECT ingredient_id 
                                FROM sad_ingredients 
                                WHERE ingredient_source = 'common'
                                )
                            )
                            ) 
                        GROUP BY ci.id
                          """)
    missing_ingredients = db.session.execute(missingquery, {"user_id": current_user.id}).fetchall()

    amountsquery = text("""
                        SELECT ca.cocktail_id, ca.ingredient_id, ca.amount, ca.ingredient_source, cc.name
                        FROM common_amounts ca
                        LEFT JOIN common_cocktails cc ON ca.cocktail_id = cc.id
                        UNION 
                        SELECT a.cocktail_id, a.ingredient_id, a.amount, a.ingredient_source, c.name
                        FROM amounts a
                        LEFT JOIN cocktails c ON a.cocktail_id = c.id
                        WHERE a.user_id = :user_id
                        """)
    amounts = db.session.execute(amountsquery, {"user_id": current_user.id}).fetchall()

    
    return render_template(
        "missingoneall.html", cocktails=cocktails, amounts=amounts, missing_ingredients=missing_ingredients, defaults=session["defaults"]
    )

@view.route("/missingoneuser")
@login_required
def missingoneuser():

    # Find cocktails missing one ingredient
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
    if not cocktails:
        return render_template("errors/no_cocktails.html")
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
                        # Main Query
                        SELECT i.id, i.name, 'user' AS source 
                        FROM ingredients i 
                        WHERE 
                            (stock != 1 AND 
                            (i.id IN 
                                (
                                SELECT ingredient_id 
                                FROM sad_ingredients 
                                WHERE ingredient_source = 'user'
                                ) 
                            )
                            ) 
                        
                        UNION 

                        SELECT ci.id, ci.name, 'common' AS source 
                        FROM common_ingredients ci 
                        JOIN common_stock cs ON ci.id = cs.ingredient_id 
                        WHERE 
                            (cs.stock != 1 AND cs.user_id = :user_id AND 
                            (ci.id IN 
                                (
                                SELECT ingredient_id 
                                FROM sad_ingredients 
                                WHERE ingredient_source = 'common'
                                )
                            )
                            ) 
                        GROUP BY ci.id
                        """)
    
    missing_ingredients = db.session.execute(missingquery, {"user_id": current_user.id}).fetchall()
   
    amountsquery = text("""
                        SELECT cocktail_id, ingredient_id, amount, ingredient_source 
                        FROM amounts 
                        WHERE user_id = :user_id
                        """)
    amounts = db.session.execute(amountsquery, {"user_id": current_user.id}).fetchall()

    return render_template(
        "missingoneuser.html", cocktails=cocktails, amounts=amounts, missing_ingredients=missing_ingredients
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
    if not cocktails:
        return render_template("errors/no_cocktails.html")

    families = set(Cocktail.family for Cocktail in cocktails)

    return render_template(
        "whatstodrinkuser.html", cocktails=cocktails, families=families
    )


@view.route("/whatstodrinkall")
@login_required
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
    if not cocktails:
        return render_template("errors/no_cocktails.html")

    families = set(Cocktail.family for Cocktail in cocktails)

    return render_template(
        "whatstodrinkall.html", cocktails=cocktails, families=families
        )

