from flask import current_app, url_for
from whatstodrink.__init__ import mail
from flask_mail import Message
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender=('no-reply@whatstodrink.com', current_app.config["MAIL_USERNAME"]), recipients=[user.email])
    msg.body = f"""To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will occur.
Cheers!"""
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()