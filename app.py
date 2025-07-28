from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from backend.models import db, User, Admin
import os

# --------------------- Flask App Setup --------------------- #
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Ensure instance folder exists
os.makedirs(app.instance_path, exist_ok=True)

# Store database inside instance/
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'my_app_db.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB
db.init_app(app)


# --------------------- DB Setup --------------------- #
def setup_database():
    """Create database and default admin user."""
    with app.app_context():
        db.create_all()
        create_default_admin()


def create_default_admin():
    """Insert default admin if not exists."""
    default_username = 'admin'
    default_password = 'admin123'

    existing_admin = Admin.query.filter_by(username=default_username).first()
    if not existing_admin:
        hashed_pw = generate_password_hash(default_password)
        new_admin = Admin(username=default_username, password_hash=hashed_pw)
        db.session.add(new_admin)
        db.session.commit()
        print(f"[✓] Admin '{default_username}' created.")
    else:
        print(f"[i] Admin '{default_username}' already exists.")


# --------------------- Routes --------------------- #
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Unified login for user and admin."""
    if request.method == 'POST':
        email_or_username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=email_or_username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['role'] = 'admin'
            session['username'] = admin.username
            flash("Admin login successful!", "success")
            return redirect(url_for('admin_dashboard'))

        user = User.query.filter_by(email=email_or_username).first()
        if user and check_password_hash(user.password_hash, password):
            session['role'] = 'user'
            session['username'] = user.username
            session['email'] = user.email
            flash(f"Welcome, {user.name}!", "success")
            return redirect(url_for('user_dashboard'))

        flash("Invalid credentials.", "danger")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration only."""
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        address = request.form['address']
        pincode = request.form['pincode']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(
            username=email,
            email=email,
            name=name,
            address=address,
            pincode=pincode,
            password_hash=hashed_pw
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))


@app.route('/user/dashboard')
def user_dashboard():
    if session.get('role') != 'user':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))
    return render_template('user_dashboard.html', username=session.get('username'))


@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html', username=session.get('username'))


# --------------------- Run --------------------- #
if __name__ == '__main__':
    setup_database()
    app.run(debug=True, port=5050)
