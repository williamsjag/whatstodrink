from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, ValidationError
from whatstodrink.models import Ingredient, CommonIngredient, Cocktail
from whatstodrink.__init__ import db
from sqlalchemy import select
from flask_login import current_user

class AddIngredientForm(FlaskForm):
    name = StringField('Ingredient Name', validators=[DataRequired()])
    short_name = StringField('Simplified Name (optional)')
    type = StringField('Ingredient Type', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    stock = BooleanField('In Stock:')
    submit = SubmitField('Add Ingredient')

    def validate_name(self, name):
        # query = text("SELECT name FROM ingredients WHERE name = :name AND user_id = :user_id UNION SELECT name FROM common_ingredients WHERE name = :name")
        ingredient = db.session.execute(select(Ingredient.name).where(Ingredient.name == name.data).where(Ingredient.user_id == current_user.id)).fetchall()
        commoningredient = db.session.execute(select(CommonIngredient.name).where(CommonIngredient.name == name.data)).fetchall()
       
        # ingredient = db.session.execute(query, {"name": name, "user_id": current_user.id}).fetchall()
        if ingredient or commoningredient:
            raise ValidationError("This ingredient already exists")
        
class AddCocktailForm(FlaskForm):
    name = StringField('Cocktail Name', validators=[DataRequired()])
    amount = StringField('Amount')
    ingredient = StringField('Recipe')
    build = TextAreaField('Build Instructions')
    source = StringField('Source')
    family = StringField('Cocktail Family')
    notes = TextAreaField('Notes')
    submit = SubmitField('Add Cocktail')

    def validate_name(self, name):
        cocktail = db.session.execute(select(Cocktail.name).where(Cocktail.name == name.data).where(Cocktail.user_id == current_user.id)).fetchall()

        if cocktail:
            raise ValidationError("You already have a cocktail by that name")