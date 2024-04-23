from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, ValidationError
from whatstodrink.models import Ingredient, Cocktail
from whatstodrink.__init__ import db
from sqlalchemy import select, or_
from flask_login import current_user

class ManageIngredientsForm(FlaskForm):
    stock = StringField('Stock')
    id = IntegerField('Id')
    source = StringField('Source')

class ModifyIngredientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    short_name = StringField('Simplified Name')
    type = StringField('Ingredient Type', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    id = IntegerField('Id')

    def validate_name(self, name):
        oldName = db.session.scalar(select(Ingredient.name)
                                    .where(Ingredient.id == self.id.data)
                                    .where(Ingredient.user_id == current_user.id))
        if name.data != oldName:
            newName = db.session.scalar(select(Ingredient.name).where(Ingredient.name == name.data)
                                        .where(or_(Ingredient.user_id == current_user.id, Ingredient.shared == 1))
                                        )
            if newName:
                raise ValidationError('An ingredient with that name already exists')
        else:
            pass

class DeleteForm(FlaskForm):
    id = IntegerField('Id')

class ModifyCocktailForm(FlaskForm):
    name = StringField('Cocktail Name')
    build = TextAreaField('Build Instructions')
    source = StringField('Source')
    family = SelectField('Cocktail Family', choices=[('Vermouth Cocktails', 'Vermouth Cocktails'), ('Sours', 'Sours'), ('Amaro Cocktails', 'Amaro Cocktails'), ('Old Fashioneds', 'Old Fashioneds'), ('Highballs', 'Highballs'), ('Champagne Cocktails', 'Champagne Cocktails'), ('Flips and Nogs', 'Flips and Nogs'), ('Juleps and Smashes', 'Juleps and Smashes'), ('Hot Drinks', 'Hot Drinks'), ('Orphans', 'Orphans'), ('Tiki Cocktails', 'Tiki Cocktails'), ('Duos and Trios', 'Duos and Trios')])
    notes = TextAreaField('Notes')
    id = IntegerField('Id')

    def validate_name(self, name):
        oldName = db.session.scalar(select(Cocktail.name)
                                    .where(Cocktail.id == self.id.data)
                                    .where(Cocktail.user_id == current_user.id))
        if name.data != oldName:
            newName = db.session.scalar(select(Cocktail.name)
                                        .where(Cocktail.name == name.data)
                                        .where(or_(Cocktail.user_id == current_user.id, Cocktail.shared == 1)))
                                        
            if newName:
                raise ValidationError('There is already a Cocktail with that name')
        else:
            pass