from flask import render_template, request, session, Blueprint, redirect, url_for
from whatstodrink.__init__ import db
from sqlalchemy import select, text, or_, func, and_, distinct
from whatstodrink.models import Ingredient, Cocktail, Amount, Stock, User
from whatstodrink.view.forms import ViewIngredientForm, CocktailSearchForm, ViewCocktailForm
from whatstodrink.modify.forms import ModifyCocktailForm
from flask_login import current_user, login_required
from whatstodrink.helpers import remove_accents


view = Blueprint('view', __name__)

# View ingredient modal from ManageIngredients 
@view.route("/viewingredientmodal")
@login_required
def viewingredientmodal():

    form = ViewIngredientForm()
    if request.args.get("ingredient"):
        referral = request.args.get("ingredient").lower()
        if referral:
            ingredient = db.session.scalar(select(Ingredient).where(func.lower(Ingredient.name) == referral).where(or_(Ingredient.user_id == current_user.id, Ingredient.shared == 1)))
            ingredientId = ingredient.id
    else:
        for key, value, in request.args.items():
            if key.startswith('stock_'):
                ingredient_name = key.replace('stock_', '')
            # contingency if stock not checked
            elif key.startswith('id_'):
                ingredient_name = key.replace('id_', '')    
        ingredient = db.session.scalar(select(Ingredient).where(Ingredient.name == ingredient_name).where(Ingredient.user_id == current_user.id))
        ingredientId = ingredient.id

    rows = db.session.scalars(select(Amount.cocktail_id).where(Amount.ingredient_id == ingredientId)).fetchall()
    cocktails = db.session.scalars(select(Cocktail.name).where(Cocktail.id.in_(rows)).limit(10)).fetchall()
    allcocktails = db.session.scalars(select(Cocktail.name).where(Cocktail.id.in_(rows))).fetchall() 

    return render_template("viewingredientmodal.html", form=form, ingredient=ingredient, cocktails=cocktails, allcocktails=allcocktails)

# Ingredient Search Box from Add Cocktail
@view.route("/ingredientsearch")
@login_required
def ingredientsearch():
    q = request.args.get("q").lower()

    if q:
        results = db.session.scalars(select(Ingredient.name)
                                     .where(func.lower(Ingredient.name).like('%' + q + '%'))
                                     .where(or_(Ingredient.user_id == current_user.id, Ingredient.shared == 1))
                                     .limit(10)
        ).fetchall()        
    else:
        results = []

    return render_template("ingredientsearch.html", results=results)

# Source search from add cocktail
@view.route("/sourcesearch")
@login_required
def sourcesearch():
    q = request.args.get("source").lower()
    print(f"{q}")

    if q:
        results = db.session.scalars(select(Cocktail.source.distinct())
                                     .where(func.lower(Cocktail.source).like('%' + q + '%'))
                                     .where(Cocktail.user_id == current_user.id)
                                     .limit(5)
        ).fetchall()        
    else:
        results = []

    return render_template("ingredientsearch.html", results=results)

@view.route("/viewcocktailmodal")
@login_required
def viewcocktailmodal():

    if request.args.get("cocktail"):
        target = request.args.get("cocktail").lower()
        if request.args.get("ingredient"):
            ingredient = request.args.get("ingredient").lower()
            if target:
                cocktail = db.session.scalar(select(Cocktail)
                                            .where(func.lower(Cocktail.name) == target)
                                            .where(or_(Cocktail.user_id == current_user.id, Cocktail.shared ==  1)))
                form = ViewCocktailForm()
                formatted_recipe = cocktail.recipe.replace(chr(31), ' ')
                return render_template("viewcocktailmodal.html", cocktail=cocktail, form=form, ingredient=ingredient, formatted_recipe=formatted_recipe)
       
    else:
        redirect(url_for("modify.manageingredients"))

@view.route("/viewcocktails", methods=["GET"])
@login_required
def viewcocktails():
   
    form2 = CocktailSearchForm()
    session["view"] = "/viewcocktails"
    if 'defaults' not in session:
        session["defaults"] = db.session.scalar(select(User.default_cocktails).where(User.id == current_user.id))
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

    # If filter bar used
    if request.method == "POST":
        filter = filter.lower()
        q = remove_accents(q.lower())

        if filter == 'search' or filter == 'search all':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in remove_accents(getattr(cocktail, attr).lower()) for attr in ['name', 'build', 'source', 'notes', 'family', 'recipe', 'ingredient_list'])
            ]
        elif filter == 'ingredient':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in remove_accents(getattr(cocktail, attr).lower()) for attr in ['recipe', 'ingredient_list'])
            ]
        else:
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if getattr(cocktail, filter) is not None and q in remove_accents(getattr(cocktail, filter).lower())
            ]

        cocktails = filtered_cocktails

        if not cocktails:
            return render_template("errors/no_cocktails.html")
        
        sorts = set(Cocktail.family for Cocktail in cocktails)       
        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        for cocktail in cocktails:
            if cocktail.recipe:
                recipe_parts = []
                for item in cocktail.recipe.split('\n'):
                    if chr(31) in item:
                        parts = item.split(chr(31))
                        recipe_parts.append((parts[0], parts[1] if len(parts) > 1 else ''))
                    else:
                        recipe_parts.append((item, ''))
                setattr(cocktail, 'recipe_parts', recipe_parts)
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form, form2=form2
            )

    # no search bar
    else:
        form = ModifyCocktailForm()
        sorts = db.session.scalars(select(Cocktail.family.distinct())).fetchall()
        form2 = CocktailSearchForm()

        for cocktail in cocktails:
            if cocktail.recipe:
                recipe_parts = []
                for item in cocktail.recipe.split('\n'):
                    if chr(31) in item:
                        parts = item.split(chr(31))
                        recipe_parts.append((parts[0], parts[1] if len(parts) > 1 else ''))
                    else:
                        recipe_parts.append((item, ''))
                setattr(cocktail, 'recipe_parts', recipe_parts)

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
        q = remove_accents(q.lower())

        if filter == 'search' or filter == 'search all':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in remove_accents(getattr(cocktail, attr).lower()) for attr in ['name', 'build', 'source', 'notes', 'family', 'recipe', 'ingredient_list'])
            ]
        elif filter == 'ingredient':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in remove_accents(getattr(cocktail, attr).lower()) for attr in ['recipe', 'ingredient_list'])
            ]
        else:
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if getattr(cocktail, filter) is not None and q in remove_accents(getattr(cocktail, filter).lower())
            ]

        cocktails = filtered_cocktails

        if not cocktails:
            return render_template("errors/no_cocktails.html")
        
        
        sorts = set(Cocktail.family for Cocktail in cocktails)

        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        for cocktail in cocktails:
            if cocktail.recipe:
                recipe_parts = []
                for item in cocktail.recipe.split('\n'):
                    if chr(31) in item:
                        parts = item.split(chr(31))
                        recipe_parts.append((parts[0], parts[1] if len(parts) > 1 else ''))
                    else:
                        recipe_parts.append((item, ''))
                setattr(cocktail, 'recipe_parts', recipe_parts)
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form, form2=form2
            )
    
    # no filter bar
    else:

        sorts = set(Cocktail.family for Cocktail in cocktails)
        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        for cocktail in cocktails:
            if cocktail.recipe:
                recipe_parts = []
                for item in cocktail.recipe.split('\n'):
                    if chr(31) in item:
                        parts = item.split(chr(31))
                        recipe_parts.append((parts[0], parts[1] if len(parts) > 1 else ''))
                    else:
                        recipe_parts.append((item, ''))
                setattr(cocktail, 'recipe_parts', recipe_parts)
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
        q = remove_accents(q.lower())

        if filter == 'search' or filter == 'search all':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in remove_accents(getattr(cocktail, attr).lower()) for attr in ['name', 'build', 'source', 'notes', 'family', 'recipe', 'ingredient_list'])
            ]
        elif filter == 'ingredient':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in remove_accents(getattr(cocktail, attr).lower()) for attr in ['recipe', 'ingredient_list'])
            ]
        else:
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if getattr(cocktail, filter) is not None and q in remove_accents(getattr(cocktail, filter).lower())
            ]

        cocktails = filtered_cocktails

        if not cocktails:
            return render_template("errors/no_cocktails.html")
        
        sorts = set(Cocktail.family for Cocktail in cocktails)
        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        for cocktail in cocktails:
            if cocktail.recipe:
                recipe_parts = []
                for item in cocktail.recipe.split('\n'):
                    if chr(31) in item:
                        parts = item.split(chr(31))
                        recipe_parts.append((parts[0], parts[1] if len(parts) > 1 else ''))
                    else:
                        recipe_parts.append((item, ''))
                setattr(cocktail, 'recipe_parts', recipe_parts)
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form, form2=form2
            )
    else:
        familyquery = text("SELECT DISTINCT family FROM cocktails WHERE shared = 1")
        sorts = db.session.scalars(familyquery).fetchall()
        for cocktail in cocktails:
            if cocktail.recipe:
                recipe_parts = []
                for item in cocktail.recipe.split('\n'):
                    if chr(31) in item:
                        parts = item.split(chr(31))
                        recipe_parts.append((parts[0], parts[1] if len(parts) > 1 else ''))
                    else:
                        recipe_parts.append((item, ''))
                setattr(cocktail, 'recipe_parts', recipe_parts)
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form
        )

@view.route("/missingone")
@login_required
def missingone():
   
    session["view"] = "/missingone"
    if 'defaults' not in session:
        session["defaults"] = db.session.scalar(select(User.default_cocktails).where(User.id == current_user.id))
    return render_template(
        "missingone.html", defaults=session["defaults"], view=session["view"]
    )

@view.route("/missingoneall")
@login_required
def missingoneall():

    # get cocktails missing exactly one ingredient
    subquery = (
        select(Amount.cocktail_id, func.count(Amount.ingredient_id).label('missing_count'))
        .join(Ingredient, Amount.ingredient_id == Ingredient.id)
        .join(Stock, and_(Stock.ingredient_id == Ingredient.id, Stock.user_id == current_user.id, Stock.stock == 0))
        .group_by(Amount.cocktail_id)
        .subquery()
    )
    cocktailquery = (
        select(Cocktail)
        .join(subquery, subquery.c.cocktail_id == Cocktail.id)
        .where(and_(subquery.c.missing_count == 1, or_(Cocktail.user_id == current_user.id, Cocktail.shared == 1)))
    )
    cocktails = db.session.scalars(cocktailquery).fetchall()

    missing_ingredients = []
    counts = {}
    
    for cocktail in cocktails:
        # Find the missing ingredient in each cocktail
        ingredient = db.session.scalar(select(Ingredient)
                                        .join(Amount, Ingredient.id == Amount.ingredient_id)
                                        .join(Stock, and_(Ingredient.id == Stock.ingredient_id, Stock.user_id == current_user.id))
                                        .where(Amount.cocktail_id == cocktail.id, Stock.stock != 1)
                                        )
        setattr(cocktail, 'ingredient_name', ingredient.name)
        # Keep track of the number of times an ingredient is missing
        if ingredient not in counts:
            counts[ingredient] = 1
        else:
            counts[ingredient] += 1
        if cocktail.recipe:
                recipe_parts = []
                for item in cocktail.recipe.split('\n'):
                    if chr(31) in item:
                        parts = item.split(chr(31))
                        recipe_parts.append((parts[0], parts[1] if len(parts) > 1 else ''))
                    else:
                        recipe_parts.append((item, ''))
                setattr(cocktail, 'recipe_parts', recipe_parts)

    for ingredient, count in counts.items():
        setattr(ingredient, "count", count)
        missing_ingredients.append(ingredient)

    missing_ingredients.sort(key=lambda x: x.count, reverse=True)

    form = ModifyCocktailForm()
    if 'defaults' not in session:
        session["defaults"] = db.session.scalar(select(User.default_cocktails).where(User.id == current_user.id))
    return render_template(
        "missingone_view.html", cocktails=cocktails, missing_ingredients=missing_ingredients, defaults=session["defaults"], form=form
    )

@view.route("/missingoneuser")
@login_required
def missingoneuser():

    # get cocktails missing exactly one ingredient
    subquery = (
        select(Amount.cocktail_id, func.count(Amount.ingredient_id).label('missing_count'))
        .join(Ingredient, Amount.ingredient_id == Ingredient.id)
        .join(Stock, and_(Stock.ingredient_id == Ingredient.id, Stock.user_id == current_user.id, Stock.stock == 0))
        .group_by(Amount.cocktail_id)
        .subquery()
    )
    cocktailquery = (
        select(Cocktail)
        .join(subquery, subquery.c.cocktail_id == Cocktail.id)
        .where(and_(subquery.c.missing_count == 1, Cocktail.user_id == current_user.id))
    )
    cocktails = db.session.scalars(cocktailquery).fetchall()

    missing_ingredients = []
    counts = {}
    
    for cocktail in cocktails:
        ingredient = db.session.scalar(select(Ingredient)
                                        .join(Amount, Ingredient.id == Amount.ingredient_id)
                                        .join(Stock, and_(Ingredient.id == Stock.ingredient_id, Stock.user_id == current_user.id))
                                        .where(Amount.cocktail_id == cocktail.id, Stock.stock != 1)
                                        )
        setattr(cocktail, 'ingredient_name', ingredient.name)
        if ingredient not in counts:
            counts[ingredient] = 1
        else:
            counts[ingredient] += 1
        if cocktail.recipe:
                recipe_parts = []
                for item in cocktail.recipe.split('\n'):
                    if chr(31) in item:
                        parts = item.split(chr(31))
                        recipe_parts.append((parts[0], parts[1] if len(parts) > 1 else ''))
                    else:
                        recipe_parts.append((item, ''))
                setattr(cocktail, 'recipe_parts', recipe_parts)

    for ingredient, count in counts.items():
        setattr(ingredient, "count", count)
        missing_ingredients.append(ingredient)

    missing_ingredients.sort(key=lambda x: x.count, reverse=True)    
    form = ModifyCocktailForm()
    return render_template(
        "missingone_view.html", cocktails=cocktails, missing_ingredients=missing_ingredients, form=form
    )
    

# Whatstodrink and Related Routes 

@view.route("/whatstodrink")
@login_required
def whatstodrink():
    form2 = CocktailSearchForm()
    session["view"] = "/whatstodrink"
    if 'defaults' not in session:
        session["defaults"] = db.session.scalar(select(User.default_cocktails).where(User.id == current_user.id))
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
        q = remove_accents(q.lower())

        if filter == 'search' or filter == 'search all':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in remove_accents(getattr(cocktail, attr).lower()) for attr in ['name', 'build', 'source', 'notes', 'family', 'recipe', 'ingredient_list'])
            ]
        elif filter == 'ingredient':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in remove_accents(getattr(cocktail, attr).lower()) for attr in ['recipe', 'ingredient_list'])
            ]
        else:
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if getattr(cocktail, filter) is not None and q in remove_accents(getattr(cocktail, filter).lower())
            ]

        cocktails = filtered_cocktails

        if not cocktails:
            return render_template("errors/no_cocktails.html")
        
        
        sorts = set(Cocktail.family for Cocktail in cocktails)

        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        for cocktail in cocktails:
            if cocktail.recipe:
                recipe_parts = []
                for item in cocktail.recipe.split('\n'):
                    if chr(31) in item:
                        parts = item.split(chr(31))
                        recipe_parts.append((parts[0], parts[1] if len(parts) > 1 else ''))
                    else:
                        recipe_parts.append((item, ''))
                setattr(cocktail, 'recipe_parts', recipe_parts)
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form, form2=form2
            )

    else:

        sorts = set(Cocktail.family for Cocktail in cocktails)

        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        for cocktail in cocktails:
            if cocktail.recipe:
                recipe_parts = []
                for item in cocktail.recipe.split('\n'):
                    if chr(31) in item:
                        parts = item.split(chr(31))
                        recipe_parts.append((parts[0], parts[1] if len(parts) > 1 else ''))
                    else:
                        recipe_parts.append((item, ''))
                setattr(cocktail, 'recipe_parts', recipe_parts)
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
        q = remove_accents(q.lower())

        if filter == 'search' or filter == 'search all':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in remove_accents(getattr(cocktail, attr).lower()) for attr in ['name', 'build', 'source', 'notes', 'family', 'recipe', 'ingredient_list'])
            ]
        elif filter == 'ingredient':
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if any(getattr(cocktail, attr) is not None and q in remove_accents(getattr(cocktail, attr).lower()) for attr in ['recipe', 'ingredient_list'])
            ]
        else:
            filtered_cocktails = [
                cocktail for cocktail in cocktails
                if getattr(cocktail, filter) is not None and q in remove_accents(getattr(cocktail, filter).lower())
            ]

        cocktails = filtered_cocktails

        if not cocktails:
            return render_template("errors/no_cocktails.html")
        
        
        sorts = set(Cocktail.family for Cocktail in cocktails)

        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        for cocktail in cocktails:
            if cocktail.recipe:
                recipe_parts = []
                for item in cocktail.recipe.split('\n'):
                    if chr(31) in item:
                        parts = item.split(chr(31))
                        recipe_parts.append((parts[0], parts[1] if len(parts) > 1 else ''))
                    else:
                        recipe_parts.append((item, ''))
                setattr(cocktail, 'recipe_parts', recipe_parts)
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form, form2=form2
            )

        
    # If no search bar
    else:

        sorts = set(Cocktail.family for Cocktail in cocktails)

        form = ModifyCocktailForm()
        form2 = CocktailSearchForm()
        for cocktail in cocktails:
            if cocktail.recipe:
                recipe_parts = []
                for item in cocktail.recipe.split('\n'):
                    if chr(31) in item:
                        parts = item.split(chr(31))
                        recipe_parts.append((parts[0], parts[1] if len(parts) > 1 else ''))
                    else:
                        recipe_parts.append((item, ''))
                setattr(cocktail, 'recipe_parts', recipe_parts)
        return render_template(
            "cocktail_views.html", cocktails=cocktails, sorts=sorts, form=form, form2=form2
            )
