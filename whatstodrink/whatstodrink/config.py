import os

class Config:
    SESSION_PERMANENT = False
    SESSION_TYPE = 'filesystem'
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    MAIL_SERVER = 'smtp.mail.me.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_PERMANENT = False
    SESSION_TYPE = 'filesystem'
    SQLALCHEMY_DATABASE_URI = 'mysql://williamsjag.mysql.pythonanywhere-services.com/williamsjag$whatstodrink'
    SQLALCHEMY_POOL_RECYCLE = 299
    SQLALCHEMY_TRACK_MODIFICATIONS = False