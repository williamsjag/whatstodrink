from flask import render_template, request, session, Blueprint, redirect, url_for
from whatstodrink.__init__ import db
from sqlalchemy import select, text, or_, func, and_
from whatstodrink.models import Ingredient, Cocktail, Amount, Stock
from whatstodrink.view.forms import ViewIngredientForm, CocktailSearchForm
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
    q = request.args.get("q").lower()

    if q:
        results = db.session.execute(select(Ingredient.name)
                                     .where(func.lower(Ingredient.name).like('%' + q + '%'))
                                     .where(or_(Ingredient.user_id == current_user.id, Ingredient.shared == 1))
                                     .limit(10)
        ).fetchall()        
    else:
        results = []

    return render_template("ingredientsearch.html", results=results)


@view.route("/viewcocktails", methods=["GET"])
@login_required
def viewcocktails():
    form2 = CocktailSearchForm()
    session["view"] = "/viewcocktails"
    return render_template(
        "viewcocktails.html", defaults=session["defaults"], form2=form2, view=session["view"]
    )

@view.route("/viewallcocktails",  methods=["GET", "POST"])
@login_required
def viewallcocktails():

    form = CocktailSearchForm()
    cocktails = db.session.scalars(select(Cocktail).where(or_(Cocktail.user_id == current_user.id, Cocktail.shared == 1))).fetchall()
    # check for querires
    q = form.q.data
    filter = form.filter.data

    if request.method == "POST":
        filter = filter.lower()
        q = q.lower()
        if filter == 'search' or filter == 'search all':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in getattr(cocktail, attr).lower() for attr in ['name', 'build', 'source', 'notes', 'family', 'recipe', 'ingredient_list'])
            ]
        elif filter == 'ingredient':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in getattr(cocktail, attr).lower() for attr in ['recipe', 'ingredient_list'])
            ]
        else:
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if getattr(cocktail, filter) is not None and q in getattr(cocktail, filter).lower()
            ]

        cocktails = filtered_cocktails

        if not cocktails:
            return render_template("errors/no_cocktails.html")
        
        sorts = set(Cocktail.family for Cocktail in cocktails)       
        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form, form2=form2
            )

    # no search bar
    else:
        form = ModifyCocktailForm()
        sorts = db.session.scalars(select(Cocktail.family.distinct())).fetchall()
        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        return render_template(
            "cocktail_views.html",  sorts=sorts, cocktails=cocktails, form=form, form2=form2
        )

@view.route("/viewuser", methods=["GET", "POST"])
@login_required
def viewuser():

    form = CocktailSearchForm()
    q = form.q.data
    filter = form.filter.data
   
    cocktails = db.session.scalars(select(Cocktail).where(Cocktail.user_id == current_user.id)).fetchall()

    if not cocktails:
        return render_template("errors/no_cocktails.html")
    
    if request.method == "POST":
        filter = filter.lower()
        q = q.lower()
        if filter == 'search' or filter == 'search all':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in getattr(cocktail, attr).lower() for attr in ['name', 'build', 'source', 'notes', 'family', 'recipe', 'ingredient_list'])
            ]
        elif filter == 'ingredient':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in getattr(cocktail, attr).lower() for attr in ['recipe', 'ingredient_list'])
            ]
        else:
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if getattr(cocktail, filter) is not None and q in getattr(cocktail, filter).lower()
            ]

        cocktails = filtered_cocktails

        if not cocktails:
            return render_template("errors/no_cocktails.html")
        
        
        sorts = set(Cocktail.family for Cocktail in cocktails)

        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form, form2=form2
            )
    
    # no filter bar
    else:

        sorts = set(Cocktail.family for Cocktail in cocktails)
        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form
        )

@view.route("/viewcommon", methods=["GET", "POST"])
@login_required
def viewcommon():
    form = CocktailSearchForm()
    q = form.q.data
    filter = form.filter.data
    cocktails = db.session.scalars(select(Cocktail).where(Cocktail.shared == 1)).fetchall()

    if request.method == "POST":
        filter = filter.lower()
        q = q.lower()

        if filter == 'search' or filter == 'search all':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in getattr(cocktail, attr).lower() for attr in ['name', 'build', 'source', 'notes', 'family', 'recipe', 'ingredient_list'])
            ]
        elif filter == 'ingredient':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in getattr(cocktail, attr).lower() for attr in ['recipe', 'ingredient_list'])
            ]
        else:
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if getattr(cocktail, filter) is not None and q in getattr(cocktail, filter).lower()
            ]

        cocktails = filtered_cocktails

        if not cocktails:
            return render_template("errors/no_cocktails.html")
        
        sorts = set(Cocktail.family for Cocktail in cocktails)
        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form, form2=form2
            )
    else:
        familyquery = text("SELECT DISTINCT family FROM cocktails WHERE shared = 1")
        sorts = db.session.scalars(familyquery).fetchall()
        
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form
        )

@view.route("/missingone")
@login_required
def missingone():
   
    session["view"] = "/missingone"
    return render_template(
        "missingone.html", defaults=session["defaults"], view=session["view"]
    )

@view.route("/missingoneall")
@login_required
def missingoneall():

    cocktailquery = (
        select(Cocktail)
        .join(Amount, Cocktail.id == Amount.cocktail_id)
        .join(Ingredient, Amount.ingredient_id == Ingredient.id)
        .join(Stock, Ingredient.id == Stock.ingredient_id)
        .where(and_(Stock.stock != 1, Stock.user_id == current_user.id, or_(Cocktail.user_id == current_user.id, Cocktail.shared == 1)))
        .group_by(Cocktail.id)
        .having(func.count(Cocktail.id) == 1)
    )
    cocktails = db.session.scalars(cocktailquery).fetchall()

    missing_ingredients = []
    counts = {}
    
    for cocktail in cocktails:
        ingredient = db.session.scalar(select(Ingredient)
                                        .join(Amount, Ingredient.id == Amount.ingredient_id)
                                        .join(Stock, and_(Ingredient.id == Stock.ingredient_id, Stock.stock != 1))
                                        .where(Amount.cocktail_id == cocktail.id)
                                        )
        setattr(cocktail, 'ingredient_name', ingredient.name)
        if ingredient not in counts:
            counts[ingredient] = 1
        else:
            counts[ingredient] += 1

    for ingredient, count in counts.items():
        setattr(ingredient, "count", count)
        missing_ingredients.append(ingredient)

    missing_ingredients.sort(key=lambda x: x.count, reverse=True)

    
    
    return render_template(
        "missingone_view.html", cocktails=cocktails, missing_ingredients=missing_ingredients, defaults=session["defaults"]
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

    missing_ingredients = []
    counts = {}
    
    for cocktail in cocktails:
        ingredient = db.session.scalar(select(Ingredient)
                                        .join(Amount, Ingredient.id == Amount.ingredient_id)
                                        .join(Stock, and_(Ingredient.id == Stock.ingredient_id, Stock.stock != 1))
                                        .where(Amount.cocktail_id == cocktail.id)
                                        )
        setattr(cocktail, 'ingredient_name', ingredient.name)
        if ingredient not in counts:
            counts[ingredient] = 1
        else:
            counts[ingredient] += 1

    for ingredient, count in counts.items():
        setattr(ingredient, "count", count)
        missing_ingredients.append(ingredient)

    missing_ingredients.sort(key=lambda x: x.count, reverse=True)    

    return render_template(
        "missingone_view.html", cocktails=cocktails, missing_ingredients=missing_ingredients
    )
    

# Whatstodrink and Related Routes 

@view.route("/whatstodrink")
@login_required
def whatstodrink():
    form2 = CocktailSearchForm()
    session["view"] = "/whatstodrink"
    return render_template(
        "whatstodrink.html", defaults=session["defaults"], form2=form2, view=session["view"]
    )


@view.route("/whatstodrinkuser", methods=["GET", "POST"])
@login_required
def whatstodrinkuser():

    form = CocktailSearchForm()
    # check for search queries 
    q = form.q.data
    filter = form.filter.data

    subquery = select(func.count()).select_from(Amount).where(Amount.cocktail_id == Cocktail.id).correlate_except(Amount).scalar_subquery()
    cocktails = db.session.scalars(select(Cocktail)
                                        .join(Amount, Cocktail.id == Amount.cocktail_id)
                                        .join(Ingredient, Amount.ingredient_id == Ingredient.id)
                                        .join(Stock, and_(Ingredient.id == Stock.ingredient_id, Stock.stock == 1, Stock.user_id == current_user.id))
                                        .where(Cocktail.user_id == current_user.id)
                                        .group_by(Cocktail.id)
                                        .having(func.count() == subquery)
    ).fetchall()

    if not cocktails:
        return render_template("errors/no_cocktails.html")


    if request.method == "POST":

        filter = filter.lower()
        q = q.lower()

        if filter == 'search' or filter == 'search all':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in getattr(cocktail, attr).lower() for attr in ['name', 'build', 'source', 'notes', 'family', 'recipe', 'ingredient_list'])
            ]
        elif filter == 'ingredient':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in getattr(cocktail, attr).lower() for attr in ['recipe', 'ingredient_list'])
            ]
        else:
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if getattr(cocktail, filter) is not None and q in getattr(cocktail, filter).lower()
            ]

        cocktails = filtered_cocktails

        if not cocktails:
            return render_template("errors/no_cocktails.html")
        
        
        sorts = set(Cocktail.family for Cocktail in cocktails)

        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form, form2=form2
            )

    else:

        sorts = set(Cocktail.family for Cocktail in cocktails)

        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form, form2=form2
        )


@view.route("/whatstodrinkall", methods=["GET", "POST"])
@login_required
def whatstodrinkall():

    form = CocktailSearchForm()
    # check for search queries 
    q = form.q.data
    filter = form.filter.data

    subquery = select(func.count()).select_from(Amount).where(Amount.cocktail_id == Cocktail.id).correlate_except(Amount).scalar_subquery()
    cocktails = db.session.scalars(select(Cocktail)
                                    .join(Amount, Cocktail.id == Amount.cocktail_id)
                                    .join(Ingredient, Amount.ingredient_id == Ingredient.id)
                                    .join(Stock, and_(Ingredient.id == Stock.ingredient_id, Stock.stock == 1, Stock.user_id == current_user.id))
                                    .where(or_(Cocktail.user_id == current_user.id, Cocktail.shared == 1))
                                    .group_by(Cocktail.id)
                                    .having(func.count() == subquery)
    ).fetchall()

    if not cocktails:
        return render_template("errors/no_cocktails.html")

    if request.method == "POST":

        filter = filter.lower()
        q = q.lower()
        if filter == 'search' or filter == 'search all':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in getattr(cocktail, attr).lower() for attr in ['name', 'build', 'source', 'notes', 'family', 'recipe', 'ingredient_list'])
            ]
        elif filter == 'ingredient':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in getattr(cocktail, attr).lower() for attr in ['recipe', 'ingredient_list'])
            ]
        else:
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if getattr(cocktail, filter) is not None and q in getattr(cocktail, filter).lower()
            ]

        cocktails = filtered_cocktails

        if not cocktails:
            return render_template("errors/no_cocktails.html")
        
        
        sorts = set(Cocktail.family for Cocktail in cocktails)

        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form, form2=form2
            )

        
    # If no search bar
    else:

        sorts = set(Cocktail.family for Cocktail in cocktails)

        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form, form2=form2
            )
