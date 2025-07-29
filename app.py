# app.py
import os
from datetime import datetime

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------
from backend.models import (
    db, User, Admin,
    ParkingLot, ParkingSpot, Reservation
)

# ------------------------------------------------------------------
# Factory
# ------------------------------------------------------------------
def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY='your_secret_key_here',
        SQLALCHEMY_DATABASE_URI='sqlite:///' +
            os.path.join(app.instance_path, 'my_app_db.sqlite3'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    # --------------------------------------------------------------
    # create tables + default admin every time the app starts
    # --------------------------------------------------------------
    def _ensure_default_admin() -> None:
        if not Admin.query.filter_by(username='admin').first():
            db.session.add(
                Admin(
                    username='admin',
                    password_hash=generate_password_hash('admin123')
                )
            )
            db.session.commit()

    with app.app_context():
        db.create_all()
        _ensure_default_admin()

    # ==============================================================
    # ROUTES
    # ==============================================================

    @app.route('/')
    def index():
        return redirect(url_for('login'))

    # ----------------------------  AUTH  --------------------------
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            login_id = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            admin = Admin.query.filter_by(username=login_id).first()
            if admin and check_password_hash(admin.password_hash, password):
                session.clear()
                session.update({'role': 'admin', 'username': admin.username})
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin_dashboard'))

            user = User.query.filter_by(email=login_id).first()
            if user and check_password_hash(user.password_hash, password):
                session.clear()
                session.update({
                    'role': 'user',
                    'username': user.username,
                    'email': user.email
                })
                flash(f'Welcome, {user.name}!', 'success')
                return redirect(url_for('user_dashboard'))

            flash('Invalid credentials.', 'danger')
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            data = {k: request.form.get(k, '').strip()
                    for k in ('email', 'name', 'address', 'pincode', 'password')}

            missing = [k for k, v in data.items() if not v]
            if missing:
                flash(f"Missing field(s): {', '.join(missing)}", 'danger')
                return redirect(url_for('register'))

            if User.query.filter_by(email=data['email']).first():
                flash('Email already registered.', 'danger')
                return redirect(url_for('register'))

            db.session.add(
                User(
                    username=data['email'],
                    email=data['email'],
                    name=data['name'],
                    address=data['address'],
                    pincode=data['pincode'],
                    password_hash=generate_password_hash(data['password'])
                )
            )
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash('Logged out successfully.', 'info')
        return redirect(url_for('login'))

    # -----------------------  ADMIN DASHBOARD  --------------------
    # -----------------------  ADMIN DASHBOARD  --------------------
    @app.route('/admin/dashboard')
    def admin_dashboard():
        # Allow only admins
        if session.get('role') != 'admin':
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('login'))

        # ---------- Quick-stat queries ----------
        total_lots      = ParkingLot.query.count()
        total_spots     = ParkingSpot.query.count()
        occupied_spots  = ParkingSpot.query.filter_by(status='O').count()
        available_spots = total_spots - occupied_spots
        # ----------------------------------------

        return render_template(
            'admin_dashboard.html',
            username=session.get('username'),
            total_lots=total_lots,
            total_spots=total_spots,
            occupied_spots=occupied_spots,
            available_spots=available_spots
        )


    # -------------------  ADMIN LOT MANAGEMENT  -------------------
    @app.route('/admin/manage-lots')
    def admin_manage_lots():
        if session.get('role') != 'admin':
            return redirect(url_for('login'))

        lots = ParkingLot.query.all()
        for lot in lots:
            lot.occupied_count = (
                ParkingSpot.query
                .filter_by(lot_id=lot.id, status='O')
                .count()
            )
        return render_template('admin_lots.html', lots=lots)

    @app.route('/admin/add-lot', methods=['GET', 'POST'])
    def admin_add_lot():
        if session.get('role') != 'admin':
            return redirect(url_for('login'))

        if request.method == 'POST':
            name      = request.form['name']
            price     = float(request.form['price'])
            address   = request.form['address']
            pincode   = request.form['pincode']
            max_spots = int(request.form['max_spots'])

            lot = ParkingLot(
                prime_location_name=name,
                price=price,
                address=address,
                pincode=pincode,
                max_spots=max_spots
            )
            db.session.add(lot)
            db.session.flush()      # lot.id available now

            for _ in range(max_spots):
                db.session.add(ParkingSpot(lot_id=lot.id, status='A'))

            db.session.commit()
            flash('New parking lot created with spots.', 'success')
            return redirect(url_for('admin_manage_lots'))

        return render_template('admin_add_lot.html')

       # --------------------  ADMIN DELETE LOT  ---------------------
# --------------------  ADMIN DELETE LOT  ---------------------
    @app.route('/admin/delete-lot/<int:lot_id>', methods=['POST'])
    def admin_delete_lot(lot_id):
        if session.get('role') != 'admin':
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('login'))

        lot = ParkingLot.query.get_or_404(lot_id)

        # How many spots are still occupied?
        occupied = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()

        if occupied > 0:
            flash(f'Cannot delete "{lot.prime_location_name}" – '
                  f'{occupied} spot(s) still occupied.', 'warning')
            return redirect(url_for('admin_manage_lots'))

        # Safe to delete (all spots available)
        db.session.delete(lot)  # cascades to spots
        db.session.commit()
        flash('Lot and all its spots deleted.', 'success')
        return redirect(url_for('admin_manage_lots'))






    # -------------------  ADMIN USER MANAGEMENT  -------------------
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
        flash('User and their reservations deleted.', 'info')
        return redirect(url_for('admin_manage_users'))

    @app.route('/admin/summary')
    def admin_summary():
        if session.get('role') != 'admin':
            return redirect(url_for('login'))

        lots        = ParkingLot.query.all()
        total_spots = ParkingSpot.query.count()
        occupied    = ParkingSpot.query.filter_by(status='O').count()
        available   = ParkingSpot.query.filter_by(status='A').count()

        revenue_data = []
        for lot in lots:
            occ = ParkingSpot.query.filter_by(
                lot_id=lot.id, status='O').count()
            revenue_data.append(
                (lot.prime_location_name, round(lot.price * occ, 2))
            )

        return render_template('admin_summary.html',
                               revenue_data=revenue_data,
                               total_spots=total_spots,
                               occupied=occupied,
                               available=available)

    @app.route('/admin/edit-lot/<int:lot_id>', methods=['GET', 'POST'])
    def admin_edit_lot(lot_id):
        if session.get('role') != 'admin':
            return redirect(url_for('login'))

        lot = ParkingLot.query.get_or_404(lot_id)

        if request.method == 'POST':
            # read form fields
            lot.prime_location_name = request.form['name']
            lot.price               = float(request.form['price'])
            lot.address             = request.form['address']
            lot.pincode             = request.form['pincode']

            # handle change in maximum spots
            new_max = int(request.form['max_spots'])
            diff    = new_max - lot.max_spots

            if diff > 0:
                # need extra spots
                for _ in range(diff):
                    db.session.add(ParkingSpot(lot_id=lot.id, status='A'))
            elif diff < 0:
                # shrinking lot
                occ = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
                if new_max < occ:
                    flash('Cannot reduce below current occupied spots.', 'danger')
                    return redirect(url_for('admin_edit_lot', lot_id=lot_id))

                # delete extra spots (only those currently available)
                to_delete = (
                    ParkingSpot.query
                    .filter_by(lot_id=lot.id, status='A')
                    .limit(-diff)
                    .all()
                )
                for spot in to_delete:
                    db.session.delete(spot)

            lot.max_spots = new_max
            db.session.commit()
            flash('Parking-lot details updated.', 'success')
            return redirect(url_for('admin_manage_lots'))

        return render_template('admin_edit_lot.html', lot=lot)
    
        # ---------- ADMIN • View all spots in a lot ----------
    @app.route('/admin/lot/<int:lot_id>/spots')
    def admin_view_spots(lot_id):
        if session.get('role') != 'admin':
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('login'))

        lot = ParkingLot.query.get_or_404(lot_id)
        spots = (
            ParkingSpot.query
            .filter_by(lot_id=lot.id)
            .order_by(ParkingSpot.id)
            .all()
        )

        spot_info = []
        for sp in spots:
            res = None
            if sp.status == 'O':
                res = (
                    Reservation.query
                    .filter_by(spot_id=sp.id, status='O')
                    .order_by(Reservation.parking_timestamp.desc())
                    .first()
                )
            spot_info.append({'spot': sp, 'reservation': res})

        # a quick header count (nice to show)
        occupied = sum(1 for i in spot_info if i['spot'].status == 'O')
        available = lot.max_spots - occupied

        return render_template(
            'admin_spots.html',
            lot=lot,
            spot_info=spot_info,
            occupied=occupied,
            available=available
        )


    # ---------------------------  USER  ----------------------------
    @app.route('/user/dashboard')
    def user_dashboard():
        if session.get('role') != 'user':
            flash('Please login as user.', 'warning')
            return redirect(url_for('login'))

        current_user = User.query.filter_by(
            username=session['username']).first()
        lots = ParkingLot.query.all()
        for lot in lots:
            lot.occupied_count = (
                ParkingSpot.query
                .filter_by(lot_id=lot.id, status='O')
                .count()
            )

        reservations = (
            Reservation.query
            .filter_by(user_id=current_user.id)
            .order_by(Reservation.parking_timestamp.desc())
            .all()
        )
        return render_template('user_dashboard.html',
                               user=current_user,
                               lots=lots,
                               reservations=reservations)

    @app.route('/user/book/<int:lot_id>', methods=['GET', 'POST'])
    def user_book_spot(lot_id):
        if session.get('role') != 'user':
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=session['username']).first()
        spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').first()

        if not spot:
            flash('No vacant spots in this location.', 'info')
            return redirect(url_for('user_dashboard'))

        if request.method == 'POST':
            vehicle_number = request.form['vehicle_number']
            expected_end_time = request.form.get('expected_end_time')

            expected_end = None
            if expected_end_time:
                expected_end = datetime.fromisoformat(expected_end_time)

            db.session.add(
                Reservation(
                    user_id=user.id,
                    spot_id=spot.id,
                    vehicle_number=vehicle_number,
                    parking_timestamp=datetime.utcnow(),
                    expected_end_time=expected_end,
                    parking_cost=0.0,
                    payment_status='Pending',
                    status='O'
                )
            )
            spot.status = 'O'
            db.session.commit()
            flash('Spot booked successfully.', 'success')
            return redirect(url_for('user_dashboard'))

        return render_template('book_spot.html', lot_id=lot_id, spot_id=spot.id)


    @app.route('/user/release/<int:spot_id>', methods=['GET', 'POST'])
    def user_release_spot(spot_id):
        if session.get('role') != 'user':
            flash('Login required.', 'danger')
            return redirect(url_for('login'))

        spot = ParkingSpot.query.get_or_404(spot_id)
        reservation = (
            Reservation.query
            .filter_by(spot_id=spot.id)
            .order_by(Reservation.parking_timestamp.desc())
            .first()
        )
        lot = ParkingLot.query.get(spot.lot_id)

        if request.method == 'POST' and spot.status == 'O':
            payment_mode = request.form.get('payment_mode')

            spot.status = 'A'
            reservation.leaving_timestamp = datetime.utcnow()
            hours = (
                reservation.leaving_timestamp - reservation.parking_timestamp
            ).total_seconds() / 3600
            cost = round(hours * lot.price, 2)

            reservation.parking_cost = cost
            reservation.payment_status = 'Paid'
            reservation.payment_mode = payment_mode
            reservation.payment_time = datetime.utcnow()
            reservation.status = 'A'
            db.session.commit()

            flash(f'Spot released. Payment of ₹{cost} via {payment_mode} completed.', 'success')
            return redirect(url_for('user_dashboard'))

        est_time = datetime.utcnow()
        est_cost = round(
            ((est_time - reservation.parking_timestamp).total_seconds() / 3600)
            * lot.price, 2
        )
        return render_template('release_confirm.html', spot=spot, cost=est_cost, lot=lot)

    @app.route('/user/search', methods=['GET', 'POST'])
    def user_search():
        if session.get('role') != 'user':
            flash('Please login to search.', 'warning')
            return redirect(url_for('login'))

        query = request.form.get('query', '')
        lots = ParkingLot.query.filter(
            (ParkingLot.prime_location_name.ilike(f'%{query}%')) |
            (ParkingLot.address.ilike(f'%{query}%')) |
            (ParkingLot.pincode.ilike(f'%{query}%'))
        ).all()
        for lot in lots:
            lot.occupied_count = (
                ParkingSpot.query
                .filter_by(lot_id=lot.id, status='O')
                .count()
            )
        return render_template('user_dashboard.html',
                               lots=lots,
                               username=session['username'])

    @app.route('/user/edit-profile', methods=['GET', 'POST'])
    def user_edit_profile():
        if session.get('role') != 'user':
            flash('Login required!', 'warning')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=session['username']).first()
        if request.method == 'POST':
            user.name    = request.form['name']
            user.address = request.form['address']
            user.pincode = request.form['pincode']
            db.session.commit()
            flash('Profile updated.', 'success')
            return redirect(url_for('user_dashboard'))

        return render_template('edit_profile.html', user=user)

          # ---------------- USER SUMMARY (personal view) ---------------
    @app.route('/user/summary')
    def user_summary():
        if session.get('role') != 'user':
            flash('Access denied!', 'danger')
            return redirect(url_for('login'))

        current_user = User.query.filter_by(username=session['username']).first()

        # every reservation ever made by this user
        reservations = (
            Reservation.query
            .filter_by(user_id=current_user.id)
            .order_by(Reservation.parking_timestamp.desc())
            .all()
        )

        # ---- aggregate personal spending by lot  ----
        spending_by_lot = {}        # {lot_name: ₹total_spent}
        visits_by_lot   = {}        # {lot_name: number_of_times}
        total_spent     = 0.0

        for r in reservations:
            lot_name = r.spot.lot.prime_location_name     # via relationships
            cost     = r.parking_cost or 0
            total_spent += cost

            spending_by_lot[lot_name] = spending_by_lot.get(lot_name, 0) + cost
            visits_by_lot[lot_name]   = visits_by_lot.get(lot_name, 0) + 1

        # convert to lists so Jinja / JS can iterate easily
        spending_chart_data = [{'name': k, 'amount': v}
                               for k, v in spending_by_lot.items()]
        visit_chart_data    = [{'name': k, 'count': v}
                               for k, v in visits_by_lot.items()]

        return render_template(
            'user_summary.html',
            reservations=reservations,
            total_spent=round(total_spent, 2),
            spending_chart_data=spending_chart_data,
            visit_chart_data=visit_chart_data
        )


    # --------------------------------------------------------------
    return app

# ------------------------------------------------------------------
# Expose for “flask run”
# ------------------------------------------------------------------
app = create_app()

# ------------------------------------------------------------------
# Allow “python app.py”
# ------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5050)
