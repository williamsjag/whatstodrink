from flask import current_app, url_for, render_template
from whatstodrink.__init__ import mail
from flask_mail import Message

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender=('no-reply@whatstodrink.com', current_app.config["MAIL_USERNAME"]), recipients=[user.email])
    msg.body = f"""To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will occur.
Cheers,
WhatsToDrink.com"""
    msg.html = render_template('email/request_reset.html', user=user, token=token)
    mail.send(msg)
