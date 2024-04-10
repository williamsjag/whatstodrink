from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from whatstodrink.models import User, Ingredient, CommonIngredient, Cocktail, CommonCocktail
from whatstodrink import db
from sqlalchemy import select, union
from flask_login import current_user
from werkzeug.security import check_password_hash


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirmation = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalars(select(User.username).where(User.username == username.data)).first()
        if user:
            raise ValidationError('That username already exists, please choose another')
    def validate_email(self, email):
        email = db.session.scalars(select(User.email).where(User.email == email.data)).first()
        if email:
            raise ValidationError('That email is already registered, please log in')

class LoginForm(FlaskForm):
    username = StringField('Email or Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

    def validate_username(self, username):
        user = db.session.scalars(select(User.username).where(User.username == username.data)).first()
        mail = db.session.scalars(select(User.email).where(User.email == username.data)).first()
        if not user or mail:
            raise ValidationError("Username or Email invalid")
        
    def validate_password(self, password):
        username = self.username.data
        user = db.session.scalars(select(User).where(User.username == username)).first()
        mail = db.session.scalars(select(User).where(User.email == username)).first()
        if user:
            if not check_password_hash(user.hash, password.data):
                raise ValidationError("Incorrect Password")
        if mail:
            if not check_password_hash(mail.hash, password.data):
                raise ValidationError("Incorrect Password")


    
class ManageIngredientsForm(FlaskForm):
    stock = StringField('Stock')
    id = IntegerField('Id')
    source = StringField('Source')

class SettingsForm(FlaskForm):
    DefaultCocktails = StringField('Enable')

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
        print(f"{ingredient}")
       
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
        
class ViewIngredientForm(FlaskForm):
    name = StringField('Ingredient Name', validators=[DataRequired()])
    short_name = StringField('Simplified Name')
    type = StringField('Ingredient Type', validators=[DataRequired()])
    notes = TextAreaField('Notes')

class ModifyIngredientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    short_name = StringField('Simplified Name')
    type = StringField('Ingredient Type', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    id = IntegerField('Id')

    def validate_name(self, name):
        oldName = db.session.scalar(select(Ingredient.name).where(Ingredient.id == self.id.data).where(Ingredient.user_id == current_user.id))
        if name.data != oldName:
            newNameUser = select(Ingredient.name).where(Ingredient.name == name.data).where(Ingredient.user_id == current_user.id)
            newNameCommon = select(CommonIngredient.name).where(CommonIngredient.name == name.data)
            newName = db.session.execute(newNameUser.union(newNameCommon)).fetchall()
            if newName:
                raise ValidationError('An ingredient with that name already exists')

class DeleteForm(FlaskForm):
    id = IntegerField('Id')

class ModifyCocktailForm(FlaskForm):
    name = StringField('Cocktail Name')
    build = TextAreaField('Build Instructions')
    source = StringField('Source')
    family = SelectField('Cocktail Family', choices=[('Vermouth Cocktails', 'Vermouth Cocktails'), ('Sours', 'Sours'), ('Amaro Cocktails', 'Amaro Cocktails'), ('Old Fashioneds', 'Old Fashioneds'), ('Highballs', 'Highballs'), ('Champagne Cocktails', 'Champagne Cocktails'), ('Juleps and Smashes', 'Juleps and Smashes'), ('Hot Drinks', 'Hot Drinks'), ('Orphans', 'Orphans'), ('Tiki Cocktails', 'Tiki Cocktails'), ('Duos and Trios', 'Duos and Trios')])
    notes = TextAreaField('Notes')
    id = IntegerField('Id')

    def validate_name(self, name):
        oldName = db.session.scalar(select(Cocktail.name).where(Cocktail.id == self.id.data).where(Cocktail.user_id == current_user.id))
        print(f"'{name.data}'")
        print(f"'{oldName}'")
        if name.data != oldName:
            newNameUser = select(Cocktail.name).where(Cocktail.name == name.data).where(Cocktail.user_id == current_user.id)
            newNameCommon = select(CommonCocktail.name).where(CommonCocktail.name == name.data)
            newName = db.session.execute(newNameUser.union(newNameCommon)).fetchall()
            if newName:
                raise ValidationError('There is already a Cocktail with that name')