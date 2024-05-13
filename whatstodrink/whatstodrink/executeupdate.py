from flask_sqlalchemy import SQLAlchemy
from updatedb import update_cocktail_recipes
from __init__ import create_app

app = create_app()

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Execute the function
update_cocktail_recipes(db)