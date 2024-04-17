from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired

class ViewIngredientForm(FlaskForm):
    name = StringField('Ingredient Name', validators=[DataRequired()])
    short_name = StringField('Simplified Name')
    type = StringField('Ingredient Type', validators=[DataRequired()])
    notes = TextAreaField('Notes')