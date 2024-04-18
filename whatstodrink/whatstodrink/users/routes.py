from flask import flash, redirect, render_template, request, session, url_for, Blueprint, current_app
from whatstodrink.__init__ import db
from sqlalchemy import select, or_, update
from werkzeug.security import check_password_hash, generate_password_hash
from whatstodrink.models import User, CommonIngredient, CommonStock
from whatstodrink.users.forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm
from flask_login import login_user, current_user, logout_user, login_required
from whatstodrink.helpers import send_reset_email
from whatstodrink.config import Config


users = Blueprint('users', __name__)

@users.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    # Forget any user_id
    session.clear()
    form = RegistrationForm()

    if request.method == "POST":

        # check to see if user exists
        if form.validate_on_submit():
            # insert into users table
            hash = generate_password_hash(
                form.password.data, method="pbkdf2", salt_length=16
            )
            newuser = User(username=form.username.data, email=form.email.data, hash=hash, default_cocktails='on')
            db.session.add(newuser)
            db.session.commit()

            flash("Your account has been created! You are now able to log in", 'primary')

            return redirect(url_for('users.login'))
            
        else:
            return render_template("register.html", form=form)
    
    # if GET
    else:
        return render_template("register.html", form=form)


@users.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    # Forget any user_id
    
    form = LoginForm()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        if form.validate_on_submit():
           
            # Query database for username
            uname = form.username.data
            password = form.password.data
            query = select(User).where(or_(User.username == uname, User.email == uname))
            user = db.session.scalars(query).first()

            # Ensure username exists and password is correct
            if not user or not check_password_hash(
                user.hash, password
            ):
                flash('Login failed. Double-check username and/or password', 'warning')
                return redirect(url_for('users.login'))

            else:
                
                session.clear()
                login_user(user, remember=form.remember.data)

                # Check default cocktail setting
                session["defaults"] = user.default_cocktails

                # make sure user has stock values for all common ingredients on login
                query = select(CommonIngredient.id)
                common_ingredients = db.session.scalars(query).all()

                # get all ids in common_ingredients
                for ingredient in common_ingredients:
                    # check if user has ingredient in common_stock
                    result = db.session.scalars(select(CommonStock.ingredient_id).where(CommonStock.user_id == current_user.id).where(CommonStock.ingredient_id == ingredient)).first()

                    # if not, insert a default
                    if not result:
                        newingredient = CommonStock(ingredient_id=ingredient, user_id = current_user.id, stock='')
                        db.session.add(newingredient)
                        db.session.commit()

                # Redirect user to home page
                flash("Successfully logged in, welcome {}!".format(user.username), 'primary')

                if form.next_page.data:
                    return redirect(form.next_page.data)
                else:
                    return redirect(url_for('main.index'))
        
        else:
            return render_template("login.html", form=form)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        next_page = request.args.get('next')
        print(f"{next_page}")
        return render_template("login.html", form=form, next_page=next_page)


@users.route("/logout")
@login_required
def logout():
    """Log user out"""

    logout_user()
    flash('Logged Out', 'primary')
    # Redirect user to login form
    return redirect(url_for('users.login'))
    

@users.route("/account")
@login_required
def account():

    return render_template("account.html")



@users.route("/resetpassword", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))   

    form = RequestResetForm()

    if form.validate_on_submit():
        user = db.session.scalar(select(User).where(User.email == form.email.data))
        print(f"{user}")
        print(f"{Config.MAIL_PASSWORD}")
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
            # insert into users table
            hash = generate_password_hash(
                form.password.data, method="pbkdf2", salt_length=16
            )
            db.session.execute(
                update(User).where(User.id == user)
                .values(hash=hash)
            )
            db.session.commit()

            flash('Your password has been updated! You are now able to log in', 'primary')
            
            return redirect(url_for('users.login'))

    return render_template("resettoken.html", methods=["GET", "POST"], form=form)

