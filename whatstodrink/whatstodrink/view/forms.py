from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired

class ViewIngredientForm(FlaskForm):
    name = StringField('Ingredient Name', validators=[DataRequired()])
    short_name = StringField('Simplified Name')
    type = StringField('Ingredient Type', validators=[DataRequired()])
    notes = TextAreaField('Notes')

class CocktailSearchForm(FlaskForm):
    filter = StringField('Filter')
    q = StringField('Search')

class ViewCocktailForm(FlaskForm):
    name = StringField('Cocktail Name')
    recipe = TextAreaField('Recipe')
    build = TextAreaField('Build')
    source = StringField('Source')
    family = StringField('Family')
    notes = TextAreaField('Notes')
    