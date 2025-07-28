# app.py
import os
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from backend.models import db, User, Admin   # <- your existing models


# ---------------------------------------------------------------------
# Application-factory
# ---------------------------------------------------------------------
def create_app() -> Flask:
    """
    Creates and configures a Flask application instance.
    Using a factory keeps the CLI (`flask run`) happy and allows easy testing.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY="your_secret_key_here",

        # SQLite file lives in instance/ so it is never committed to VCS
        SQLALCHEMY_DATABASE_URI="sqlite:///" +
        os.path.join(app.instance_path, "my_app_db.sqlite3"),

        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # Ensure instance/ exists
    os.makedirs(app.instance_path, exist_ok=True)

    # -----------------------------------------------------------------
    # Database initialisation
    # -----------------------------------------------------------------
    db.init_app(app)

    def _insert_default_admin() -> None:
        """Create the default admin row exactly once."""
        default_user = "admin"
        default_pass = "admin123"

        if not Admin.query.filter_by(username=default_user).first():
            db.session.add(
                Admin(
                    username=default_user,
                    password_hash=generate_password_hash(default_pass)
                )
            )
            db.session.commit()

    # run once, right now
    with app.app_context():
        db.create_all()
        _insert_default_admin()

    # -----------------------------------------------------------------
    # Routes
    # -----------------------------------------------------------------
    @app.route("/")
    def home():
        # simple landing page
        return redirect(url_for("login"))

    # ---------------  AUTH  ----------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            login_id = request.form.get("username")
            password = request.form.get("password")

            # 1. admin?
            admin = Admin.query.filter_by(username=login_id).first()
            if admin and check_password_hash(admin.password_hash, password):
                session.clear()
                session.update({"role": "admin", "username": admin.username})
                flash("Admin login successful!", "success")
                return redirect(url_for("admin_dashboard"))

            # 2. user?
            user = User.query.filter_by(email=login_id).first()
            if user and check_password_hash(user.password_hash, password):
                session.clear()
                session.update(
                    {
                        "role": "user",
                        "username": user.username,
                        "email": user.email,
                    }
                )
                flash(f"Welcome, {user.name}!", "success")
                return redirect(url_for("user_dashboard"))

            flash("Invalid credentials.", "danger")

        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            email    = request.form.get("email")
            name     = request.form.get("name")
            address  = request.form.get("address")
            pincode  = request.form.get("pincode")
            password = request.form.get("password")

            if User.query.filter_by(email=email).first():
                flash("Email already registered.", "danger")
                return redirect(url_for("register"))

            db.session.add(
                User(
                    username=email,
                    email=email,
                    name=name,
                    address=address,
                    pincode=pincode,
                    password_hash=generate_password_hash(password),
                )
            )
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Logged out successfully.", "info")
        return redirect(url_for("login"))

    # ---------------  DASHBOARDS  ----------------
    @app.route("/user/dashboard")
    def user_dashboard():
        if session.get("role") != "user":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("login"))
        return render_template(
            "user_dashboard.html",
            username=session.get("username")
        )

    @app.route("/admin/dashboard")
    def admin_dashboard():
        if session.get("role") != "admin":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("login"))
        return render_template(
            "admin_dashboard.html",
            username=session.get("username")
        )

    return app


# ---------------------------------------------------------------------
# Expose the app object for `flask run`
# ---------------------------------------------------------------------
app = create_app()

# ---------------------------------------------------------------------
# Optional: allow `python app.py` to work as well
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5050)






