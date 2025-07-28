from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from backend.models import db, User, Admin
from backend.models import db, User, Admin, ParkingLot, ParkingSpot, Reservation

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
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


# ---------------------- Admin Functional Routes (Fixed) ----------------------

@app.route('/admin/manage-lots')
def admin_manage_lots():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    lots = ParkingLot.query.all()
    for lot in lots:
        lot.occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
    return render_template('admin_lots.html', lots=lots)


@app.route('/admin/add-lot', methods=['GET', 'POST'])
def admin_add_lot():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        address = request.form['address']
        pincode = request.form['pincode']
        max_spots = int(request.form['max_spots'])

        # Your model uses: prime_location_name, price, address, pincode, max_spots
        lot = ParkingLot(
            prime_location_name=name,
            price=price,
            address=address,
            pincode=pincode,
            max_spots=max_spots
        )
        db.session.add(lot)
        db.session.flush()  # To get lot.id before commit

        # Create empty parking spots
        for i in range(1, max_spots + 1):
            spot = ParkingSpot(lot_id=lot.id, status='A')
            db.session.add(spot)

        db.session.commit()
        flash("New parking lot created with spots.", "success")
        return redirect(url_for('admin_manage_lots'))

    return render_template('admin_add_lot.html')


@app.route('/admin/delete-lot/<int:lot_id>', methods=['POST'])
def admin_delete_lot(lot_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    lot = ParkingLot.query.get_or_404(lot_id)
    db.session.delete(lot)  # cascade will remove spots due to model
    db.session.commit()
    flash("Lot and all its spots deleted.", "warning")
    return redirect(url_for('admin_manage_lots'))


@app.route('/admin/manage-users')
def admin_manage_users():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    users = User.query.all()
    return render_template('admin_users.html', users=users)


@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    user = User.query.get_or_404(user_id)
    for res in user.reservations:
        spot = ParkingSpot.query.get(res.spot_id)
        if spot:
            spot.status = 'A'
        db.session.delete(res)
    db.session.delete(user)
    db.session.commit()
    flash("User and their reservations deleted.", "info")
    return redirect(url_for('admin_manage_users'))


@app.route('/admin/summary')
def admin_summary():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    lots = ParkingLot.query.all()
    total_spots = ParkingSpot.query.count()
    occupied = ParkingSpot.query.filter_by(status='O').count()
    available = ParkingSpot.query.filter_by(status='A').count()
    revenue_data = []

    for lot in lots:
        occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        revenue = round(lot.price * occupied_count, 2)
        revenue_data.append((lot.prime_location_name, revenue))

    return render_template('admin_summary.html',
                           revenue_data=revenue_data,
                           total_spots=total_spots,
                           occupied=occupied,
                           available=available)



# --------------------- Run --------------------- #
if __name__ == '__main__':
    setup_database()
    app.run(debug=True, port=5050)
