from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from whatstodrink.config import TestConfig, ProductionConfig
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

# Configure application
app = Flask(__name__)
app.config.from_object(TestConfig)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)

Session(app)

db = SQLAlchemy(app)

from whatstodrink import routes
