from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from whatstodrink.config import Config
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

# Configure application
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    from whatstodrink.users.routes import users
    from whatstodrink.main.routes import main
    from whatstodrink.create.routes import create
    from whatstodrink.modify.routes import modify
    from whatstodrink.view.routes import view
    app.register_blueprint(users)
    app.register_blueprint(main)
    app.register_blueprint(create)
    app.register_blueprint(modify)
    app.register_blueprint(view)

    csrf.init_app(app)
    login_manager.init_app(app)
    Session(app)
    db.init_app(app)

    @app.after_request
    def after_request(response):
        """Ensure responses aren't cached"""
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response
    
    return app
    