from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import or_
from ..extensions import db
from ..forms import LoginForm, RegisterForm
from ..models import StaffProfile, User, UserRole

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.email.data.lower().strip()
        # Allows logging in with email (e.g. manager@freshtrack.example), handle (e.g. manager), or display name
        user = User.query.join(User.profile, isouter=True).filter(
            or_(
                User.email == identifier,
                User.email.like(f"{identifier}@%"),
                StaffProfile.display_name.ilike(identifier)
            )
        ).first()

        if user and user.check_password(form.password.data) and user.is_active_account:
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back, {user.display_name}.", "success")
            return redirect(request.args.get("next") or url_for("main.dashboard"))
        flash("Email/Username or password is incorrect.", "danger")
    return render_template("auth/login.html", form=form)

@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower().strip()).first():
            flash("An account already uses that email.", "danger")
        else:
            user = User(email=form.email.data.lower().strip())
            user.set_password(form.password.data)
            user.profile = StaffProfile(display_name=form.display_name.data.strip())
            user.role_record = UserRole(role="staff")
            db.session.add(user)
            db.session.commit()
            flash("Account created. You can sign in now.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)

@bp.post("/logout")
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))
