from flask import flash, redirect, render_template, request, session, url_for, Blueprint, current_app
from whatstodrink.__init__ import db
from sqlalchemy import select, or_, update, text, exc, or_
from werkzeug.security import check_password_hash, generate_password_hash
from whatstodrink.models import User, Ingredient, Stock
from whatstodrink.users.forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm, SettingsForm
from flask_login import login_user, current_user, logout_user, login_required
from whatstodrink.helpers import send_reset_email, commit_transaction


users = Blueprint('users', __name__)

@users.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    # Forget any user_id
    session.clear()
    form = RegistrationForm()

    # check to see if user exists if form submitted
    if form.validate_on_submit():
        # insert into users table
        hash = generate_password_hash(
            form.password.data, method="pbkdf2", salt_length=16
        )
        newuser = User(username=form.username.data, email=form.email.data, hash=hash, default_cocktails=1)
        db.session.add(newuser)
        commit_transaction()
        flash("Your account has been created! You are now able to log in", 'primary')        
        return redirect(url_for('users.login'))
        
    return render_template("register.html", form=form)


@users.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    # Forget any user_id
    
    form = LoginForm()
        
    if form.validate_on_submit():
        uname = form.username.data
        user = db.session.scalar(select(User).where(or_(User.username == uname, User.email == uname)))
        if user and check_password_hash(user.hash, form.password.data):
            session.clear()
            login_user(user, remember=form.remember.data)
            # Check default cocktail setting
            session["defaults"] = user.default_cocktails

            # make sure user has stock values for all necessary ingredients on login
            common_ingredients = db.session.scalars(select(Ingredient.id).where(or_(Ingredient.shared == 1, Ingredient.user_id == current_user.id))).all()
            for ingredient in common_ingredients:
                result = db.session.scalars(select(Stock.ingredient_id).where(Stock.user_id == current_user.id).where(Stock.ingredient_id == ingredient)).first()
                # if not, insert a default
                if not result:
                    db.session.add(Stock(ingredient_id=ingredient, user_id = current_user.id, stock=0))
            commit_transaction()                    

            flash(f"{user.username} successfully logged in, welcome!", 'primary')
            return redirect(form.next_page.data or url_for('main.index'))
        else:
            flash('Login failed. Double-check username and/or password', 'warning')

    return render_template("login.html", form=form)


@users.route("/logout")
@login_required
def logout():
    """Log user out"""

    logout_user()
    flash('Logged Out', 'primary')
    return redirect(url_for('users.login'))
    

@users.route("/account",  methods=["GET", "POST"])
@login_required
def account():
    form = SettingsForm()

    if request.method == "POST":
        cocktail_setting = request.form.get('cocktailswitch')
        # cocktailupdate = text("UPDATE users SET default_cocktails = 1 WHERE id = :user_id")
        current_user.default_cocktails = cocktail_setting
        commit_transaction
        session["defaults"] = 'on' if cocktail_setting else ''

    defaults = session.get("defaults")
    if defaults is None:
        defaults = current_user.default_cocktails
        session["defaults"] = defaults
        
    return render_template("account.html", defaults=defaults, form=form)


@users.route("/resetpassword", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))   

    form = RequestResetForm()
    if form.validate_on_submit():
        user = db.session.scalar(select(User).where(User.email == form.email.data))
        if user:
            send_reset_email(user)
            flash('An email has been sent with instructions to reset your password.', 'primary')
            return redirect(url_for('users.login'))

    return render_template("resetrequest.html", form=form) 

@users.route("/resetpassword/<token>.html", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user = User.verify_reset_token(token)
    if not user:
        flash('Error: invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
            hash = generate_password_hash(form.password.data, method="pbkdf2", salt_length=16)
            db.session.execute(update(User).where(User.id == user).values(hash=hash))
            commit_transaction
            flash('Your password has been updated! You are now able to log in', 'primary')
            return redirect(url_for('users.login'))

    return render_template("resettoken.html", form=form)

