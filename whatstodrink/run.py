from whatstodrink.__init__ import create_app, db
from socket import gethostname
from flask import current_app

app = create_app()

if __name__ == '__main__':
    with current_app.app_context():
        db.create_all()
    if 'liveconsole' not in gethostname():
        app.run()