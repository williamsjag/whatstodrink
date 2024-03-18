import os

class TestConfig:
    SECRET_KEY = 'Kos4LjKheVkf3yzgvMDLubK6DHGXDqGW'
    SESSION_PERMANENT = False
    SESSION_TYPE = 'filesystem'
    SQLALCHEMY_DATABASE_URI = 'mysql://root:database@localhost/whatstodrink'

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_PERMANENT = False
    SESSION_TYPE = 'filesystem'
    SQLALCHEMY_DATABASE_URI = 'mysql://williamsjag.mysql.pythonanywhere-services.com/williamsjag$whatstodrink'
    SQLALCHEMY_POOL_RECYCLE = 299
    SQLALCHEMY_TRACK_MODIFICATIONS = False