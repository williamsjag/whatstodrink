from whatstodrink.__init__ import db, login_manager
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
    default_cocktails = db.Column(db.String(2), default="on")

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
    sequence = db.Column(db.Integer)
    amount = db.Column(db.String(50))
    ingredient_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ingredient_source = db.Column(db.String(50))

class Cocktail(db.Model):
    __tablename__ = 'cocktails'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    build = db.Column(db.String(1000))
    source = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    family = db.Column(db.String(50), default="Orphans")
    notes = db.Column(db.String(1000))
    recipe = db.Column(db.String(500))
    ingredient_list = db.Column(db.String(200))
    
class Ingredient(db.Model):
    __tablename__ = 'ingredients'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50))
    stock = db.Column(db.String(2))
    user_id = db.Column(db.Integer)
    short_name = db.Column(db.String(50))
    notes = db.Column(db.String(1000))

class CommonAmount(db.Model):
    __tablename__ = 'common_amounts'

    cocktail_id = db.Column(db.Integer, db.ForeignKey('common_cocktails.id'), primary_key=True)
    amount = db.Column(db.String(50))
    sequence = db.Column(db.Integer)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('common_ingredients.id'), primary_key=True)
    ingredient_source = db.Column(db.String(50), primary_key=True)
    
class CommonIngredient(db.Model):
    __tablename__ = 'common_ingredients'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50))
    short_name = db.Column(db.String(50))
    notes = db.Column(db.String(1000))

class CommonStock(db.Model):
    __tablename__ = 'common_stock'

    ingredient_id = db.Column(db.Integer, db.ForeignKey('common_ingredients.id'), primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True, nullable=False)
    stock = db.Column(db.String(2))
    notes = db.Column(db.String(1000))

class CommonCocktail(db.Model):
    __tablename__ = 'common_cocktails'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    build = db.Column(db.String(1000))
    source = db.Column(db.String(50))
    family = db.Column(db.String(50))
    ingredients = db.Column(db.String(500))
    ingredient_list = db.Column(db.String(200))

class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tag = db.Column(db.String(50), nullable=False)

class TagMapping(db.Model):
    __tablename__ = 'tag_mapping'

    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True, nullable=False)
    cocktail_id = db.Column(db.Integer, db.ForeignKey('cocktails.id'), primary_key = True, nullable=False)