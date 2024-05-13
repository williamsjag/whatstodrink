from sqlalchemy import select, text, update
from models import  Cocktail, Amount
from __init__ import db


def update_cocktail_recipes():
    # Retrieve all cocktails
    all_cocktails = db.session.scalars(select(Cocktail.id)).fetchall()

    for cocktail_id in all_cocktails:
        # Execute the function for each cocktail
        update_cocktail_recipe(cocktail_id)


def update_cocktail_recipe(cocktail_id):

    cocktail = db.session.scalar(select(Cocktail).where(Cocktail.id == cocktail_id))
    if cocktail:
        ingredientsq = text("""
                            SELECT * FROM (
                                    SELECT i.id, i.name, i.short_name, a.sequence
                                    FROM ingredients i
                                    LEFT JOIN amounts a ON i.id = a.ingredient_id
                                    WHERE a.cocktail_id = :cocktail
                                    ) AS subquery
                                ORDER BY sequence ASC;
                                """)
        ingredients = db.session.execute(ingredientsq, {"cocktail": cocktail.id}).fetchall()

        amounts = db.session.execute(select(Amount.ingredient_id, Amount.cocktail_id, Amount.amount, Amount.sequence)
                                     .where(Amount.cocktail_id == cocktail.id)
                                     .order_by(Amount.sequence)
        ).fetchall()

        recipe = ""
        for amount, ingredient in zip(amounts, ingredients):
            recipe += f"{amount.amount}{chr(31)}{ingredient.name}\n"
                    
        ingredient_list = ', '.join([row.short_name if row.short_name else row.name for row in ingredients])
        try:
            db.session.execute(update(Cocktail)
                               .where(Cocktail.id == cocktail.id)
                               .values(recipe=recipe, ingredient_list=ingredient_list))
            db.session.commit()
        except Exception as e:
            db.session.rollback()