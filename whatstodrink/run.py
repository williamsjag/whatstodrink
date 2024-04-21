from whatstodrink.__init__ import create_app, db
from socket import gethostname

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    if 'liveconsole' not in gethostname():
        app.run()