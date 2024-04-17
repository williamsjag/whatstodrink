from flask_wtf import FlaskForm
from wtforms import StringField

class SettingsForm(FlaskForm):
    DefaultCocktails = StringField('Enable')