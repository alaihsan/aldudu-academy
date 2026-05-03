from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from app.extensions import db
from app.models import User, UserRole

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")

        if not name or not email or len(password) < 6:
            flash("Nama, email, dan password minimal 6 karakter wajib diisi.", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("Email sudah digunakan.", "error")
            return render_template("auth/register.html")

        user = User(
            name=name,
            email=email,
            role=UserRole.TEACHER if role == "teacher" else UserRole.STUDENT,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("main.index"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Email atau password salah.", "error")
            return render_template("auth/login.html")
        login_user(user)
        return redirect(url_for("main.index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
