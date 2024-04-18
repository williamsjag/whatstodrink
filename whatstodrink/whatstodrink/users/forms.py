from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from whatstodrink.models import User
from whatstodrink.__init__ import db
from sqlalchemy import select
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
            
class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        email = db.session.scalars(select(User.email).where(User.email == email.data)).first()
        if not email:
            raise ValidationError('There is no account with that email.')
        
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirmation = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


