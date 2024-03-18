from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from whatstodrink.models import User
from whatstodrink import db
from sqlalchemy import select


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
    
class ManageIngredientsForm(FlaskForm):
    stock = StringField('Stock')
    id = IntegerField('Id')
    source = StringField('Source')

class SettingsForm(FlaskForm):
    DefaultCocktails = StringField('Enable')