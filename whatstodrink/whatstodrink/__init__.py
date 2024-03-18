from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure secret key
app.config["SECRET_KEY"] = 'NGpVnzV3nncEHgoX'

# Configure LOCAL DB connection in SQLALCHEMY if launched from 'python3 app.py'
# if __name__ == '__main__':
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:database@localhost/whatstodrink'

# Configure PYTHONANYWHERE DB connection in SQLAlchemy for MySQL
# else:
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://williamsjag.mysql.pythonanywhere-services.com/williamsjag$whatstodrink'
#     app.config['SQLALCHEMY_POOL_RECYCLE'] = 299
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from whatstodrink import routes
