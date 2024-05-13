from __init__ import db, login_manager
from flask import current_app
from flask_login import UserMixin
import jwt
from sqlalchemy import select
from time import time


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    hash = db.Column(db.String(200), nullable=False)
    default_cocktails = db.Column(db.Boolean, default=1)

    def get_reset_token(self, expires_in=900):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_token(token):
        try:
            user_id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return None
        user = db.session.scalar(select(User.id).where(User.id == user_id))
        return user

class Amount(db.Model):
    __tablename__ = 'amounts'

    cocktail_id = db.Column(db.Integer, db.ForeignKey('cocktails.id'), primary_key=True)
    sequence = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.String(50))
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Cocktail(db.Model):
    __tablename__ = 'cocktails'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    build = db.Column(db.String(1000))
    source = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    family = db.Column(db.String(50), default="Orphans")
    notes = db.Column(db.String(1000))
    recipe = db.Column(db.String(500))
    ingredient_list = db.Column(db.String(200))
    shared = db.Column(db.Boolean)

    
class Ingredient(db.Model):
    __tablename__ = 'ingredients'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db.Column(db.String(50),nullable=False)
    type = db.Column(db.String(50))
    user_id = db.Column(db.Integer)
    short_name = db.Column(db.String(50))
    notes = db.Column(db.String(1000))
    shared = db.Column(db.Boolean)

    stock = db.relationship("Stock", back_populates="ingredient")
    cocktail = db.relationship("Cocktail", secondary="amounts", backref="ingredients")

class Stock(db.Model):
    __tablename__ = 'stock'

    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True, nullable=False)
    stock = db.Column(db.Boolean)

    ingredient = db.relationship("Ingredient", back_populates="stock")

class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tag = db.Column(db.String(50), nullable=False)

class TagMapping(db.Model):
    __tablename__ = 'tag_mapping'

    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True, nullable=False)
    cocktail_id = db.Column(db.Integer, db.ForeignKey('cocktails.id'), primary_key = True, nullable=False)