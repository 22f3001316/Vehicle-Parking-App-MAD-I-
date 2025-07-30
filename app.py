# app.py
import os
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------------------------------------------------------
# Database Models Import
# ------------------------------------------------------------------
from backend.models import (
    db, User, Admin,
    ParkingLot, ParkingSpot, Reservation
)

# ------------------------------------------------------------------
# Application Factory Pattern
# ------------------------------------------------------------------
def initialize_parking_app() -> Flask:
    parking_app = Flask(__name__, instance_relative_config=True)
    
    # Configuration setup
    parking_app.config.update(
        SECRET_KEY='parking_management_secret_2024',
        SQLALCHEMY_DATABASE_URI='sqlite:///' +
            os.path.join(parking_app.instance_path, 'parking_system_db.sqlite3'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_PERMANENT=False
    )

    # Ensure instance directory exists
    os.makedirs(parking_app.instance_path, exist_ok=True)
    db.init_app(parking_app)

    # ------------------------------------------------------------------
    # Database Initialization and Default Admin Setup
    # ------------------------------------------------------------------
    def setup_initial_database_state() -> None:
        admin_exists = Admin.query.filter_by(username='admin').first()
        if not admin_exists:
            default_admin = Admin(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(default_admin)
            db.session.commit()
            print("Default admin account created successfully")

    # Initialize database with app context
    with parking_app.app_context():
        db.create_all()
        setup_initial_database_state()

    # ------------------------------------------------------------------
    # Authentication Decorators
    # ------------------------------------------------------------------
    def require_admin_access(route_function):
        @wraps(route_function)
        def decorated_route(*args, **kwargs):
            if session.get('user_role') != 'administrator':
                flash('Administrative privileges required for this action.', 'error')
                return redirect(url_for('authentication_portal'))
            return route_function(*args, **kwargs)
        return decorated_route

    def require_user_access(route_function):
        @wraps(route_function)
        def decorated_route(*args, **kwargs):
            if session.get('user_role') != 'customer':
                flash('Customer login required to access this page.', 'warning')
                return redirect(url_for('authentication_portal'))
            return route_function(*args, **kwargs)
        return decorated_route

    # ==================================================================
    # APPLICATION ROUTES DEFINITION
    # ==================================================================

    @parking_app.route('/')
    def application_home():
        return redirect(url_for('authentication_portal'))

    # ------------------------------------------------------------------
    # Authentication and Authorization Routes
    # ------------------------------------------------------------------
    @parking_app.route('/auth', methods=['GET', 'POST'])
    def authentication_portal():
        if request.method == 'POST':
            credential_id = request.form.get('credential_id', '').strip()
            access_code = request.form.get('access_code', '').strip()

            if not credential_id or not access_code:
                flash('Both username and password fields are mandatory.', 'error')
                return render_template('login.html')

            # Administrator authentication check
            admin_account = Admin.query.filter_by(username=credential_id).first()
            if admin_account and check_password_hash(admin_account.password_hash, access_code):
                session.clear()
                session.update({
                    'user_role': 'administrator', 
                    'authenticated_user': admin_account.username,
                    'login_timestamp': datetime.utcnow().isoformat()
                })
                flash('Administrator access granted successfully!', 'success')
                return redirect(url_for('admin_control_center'))

            # Customer authentication check
            customer_account = User.query.filter_by(email=credential_id).first()
            if customer_account and check_password_hash(customer_account.password_hash, access_code):
                session.clear()
                session.update({
                    'user_role': 'customer',
                    'authenticated_user': customer_account.username,
                    'customer_email': customer_account.email,
                    'login_timestamp': datetime.utcnow().isoformat()
                })
                flash(f'Welcome back, {customer_account.name}!', 'success')
                return redirect(url_for('customer_portal'))

            flash('Authentication failed. Please verify your credentials.', 'error')
        
        return render_template('login.html')

    @parking_app.route('/customer-registration', methods=['GET', 'POST'])
    def customer_registration():
        if request.method == 'POST':
            registration_data = {
                field: request.form.get(field, '').strip()
                for field in ('email', 'name', 'address', 'pincode', 'password')
            }

            # Validate required fields
            empty_fields = [field for field, value in registration_data.items() if not value]
            if empty_fields:
                flash(f"Please fill in the following required fields: {', '.join(empty_fields)}", 'error')
                return redirect(url_for('customer_registration'))

            # Check for existing email
            existing_customer = User.query.filter_by(email=registration_data['email']).first()
            if existing_customer:
                flash('An account with this email address already exists.', 'error')
                return redirect(url_for('customer_registration'))

            # Create new customer account
            new_customer = User(
                username=registration_data['email'],
                email=registration_data['email'],
                name=registration_data['name'],
                address=registration_data['address'],
                pincode=registration_data['pincode'],
                password_hash=generate_password_hash(registration_data['password'])
            )
            
            db.session.add(new_customer)
            db.session.commit()
            flash('Account created successfully. Please proceed to login.', 'success')
            return redirect(url_for('authentication_portal'))

        return render_template('register.html')

    @parking_app.route('/session-logout')
    def session_logout():
        session.clear()
        flash('You have been logged out successfully.', 'info')
        return redirect(url_for('authentication_portal'))

    # ------------------------------------------------------------------
    # Administrator Dashboard and Management Routes
    # ------------------------------------------------------------------
    @parking_app.route('/admin/control-center')
    @require_admin_access
    def admin_control_center():
        # Calculate system statistics
        facility_count = ParkingLot.query.count()
        total_parking_spots = ParkingSpot.query.count()
        currently_occupied = ParkingSpot.query.filter_by(status='O').count()
        currently_available = total_parking_spots - currently_occupied

        return render_template(
            'admin_dashboard.html',
            username=session.get('authenticated_user'),
            total_lots=facility_count,
            total_spots=total_parking_spots,
            occupied_spots=currently_occupied,
            available_spots=currently_available
        )

    @parking_app.route('/admin/facility-management')
    @require_admin_access
    def facility_management():
        parking_facilities = ParkingLot.query.all()
        
        # Calculate occupancy for each facility
        for facility in parking_facilities:
            facility.occupied_count = (
                ParkingSpot.query
                .filter_by(lot_id=facility.id, status='O')
                .count()
            )
        
        return render_template('admin_lots.html', lots=parking_facilities)

    @parking_app.route('/admin/create-facility', methods=['GET', 'POST'])
    @require_admin_access
    def create_parking_facility():
        if request.method == 'POST':
            facility_name = request.form['name']
            hourly_rate = float(request.form['price'])
            location_address = request.form['address']
            postal_code = request.form['pincode']
            capacity_limit = int(request.form['max_spots'])

            new_facility = ParkingLot(
                prime_location_name=facility_name,
                price=hourly_rate,
                address=location_address,
                pincode=postal_code,
                max_spots=capacity_limit
            )
            
            db.session.add(new_facility)
            db.session.flush()  # Get facility ID

            # Generate parking spots for the facility
            for spot_index in range(capacity_limit):
                parking_space = ParkingSpot(lot_id=new_facility.id, status='A')
                db.session.add(parking_space)

            db.session.commit()
            flash('Parking facility created successfully with all spots initialized.', 'success')
            return redirect(url_for('facility_management'))

        return render_template('admin_add_lot.html')

    @parking_app.route('/admin/remove-facility/<int:facility_id>', methods=['POST'])
    @require_admin_access
    def remove_parking_facility(facility_id):
        target_facility = ParkingLot.query.get_or_404(facility_id)

        # Check for occupied spots
        occupied_spots_count = ParkingSpot.query.filter_by(lot_id=target_facility.id, status='O').count()

        if occupied_spots_count > 0:
            flash(f'Cannot remove "{target_facility.prime_location_name}" - '
                  f'{occupied_spots_count} spot(s) currently in use.', 'warning')
            return redirect(url_for('facility_management'))

        # Safe to remove facility
        db.session.delete(target_facility)  # Cascades to related spots
        db.session.commit()
        flash('Parking facility and all associated spots removed successfully.', 'success')
        return redirect(url_for('facility_management'))

    @parking_app.route('/admin/customer-management')
    @require_admin_access
    def customer_management():
        all_customers = User.query.all()
        return render_template('admin_users.html', users=all_customers)

    @parking_app.route('/admin/remove-customer/<int:customer_id>', methods=['POST'])
    @require_admin_access
    def remove_customer_account(customer_id):
        target_customer = User.query.get_or_404(customer_id)
        
        # Handle customer's active reservations
        for booking in target_customer.reservations:
            associated_spot = ParkingSpot.query.get(booking.spot_id)
            if associated_spot:
                associated_spot.status = 'A'  # Mark spot as available
            db.session.delete(booking)
        
        db.session.delete(target_customer)
        db.session.commit()
        flash('Customer account and all associated reservations removed.', 'info')
        return redirect(url_for('customer_management'))

    @parking_app.route('/admin/system-analytics')
    @require_admin_access
    def system_analytics():
        all_facilities = ParkingLot.query.all()
        total_spaces = ParkingSpot.query.count()
        occupied_spaces = ParkingSpot.query.filter_by(status='O').count()
        available_spaces = ParkingSpot.query.filter_by(status='A').count()

        revenue_analytics = []
        for facility in all_facilities:
            occupied_count = ParkingSpot.query.filter_by(
                lot_id=facility.id, status='O').count()
            revenue_analytics.append(
                (facility.prime_location_name, round(facility.price * occupied_count, 2))
            )

        return render_template('admin_summary.html',
                               revenue_data=revenue_analytics,
                               total_spots=total_spaces,
                               occupied=occupied_spaces,
                               available=available_spaces)

    @parking_app.route('/admin/modify-facility/<int:facility_id>', methods=['GET', 'POST'])
    @require_admin_access
    def modify_parking_facility(facility_id):
        target_facility = ParkingLot.query.get_or_404(facility_id)

        if request.method == 'POST':
            # Update facility information
            target_facility.prime_location_name = request.form['name']
            target_facility.price = float(request.form['price'])
            target_facility.address = request.form['address']
            target_facility.pincode = request.form['pincode']

            # Handle capacity changes
            new_capacity = int(request.form['max_spots'])
            capacity_difference = new_capacity - target_facility.max_spots

            if capacity_difference > 0:
                # Add new spots
                for _ in range(capacity_difference):
                    new_spot = ParkingSpot(lot_id=target_facility.id, status='A')
                    db.session.add(new_spot)
            elif capacity_difference < 0:
                # Reduce capacity
                current_occupied = ParkingSpot.query.filter_by(lot_id=target_facility.id, status='O').count()
                if new_capacity < current_occupied:
                    flash('Cannot reduce capacity below currently occupied spots.', 'error')
                    return redirect(url_for('modify_parking_facility', facility_id=facility_id))

                # Remove available spots
                spots_to_remove = (
                    ParkingSpot.query
                    .filter_by(lot_id=target_facility.id, status='A')
                    .limit(-capacity_difference)
                    .all()
                )
                for spot in spots_to_remove:
                    db.session.delete(spot)

            target_facility.max_spots = new_capacity
            db.session.commit()
            flash('Parking facility updated successfully.', 'success')
            return redirect(url_for('facility_management'))

        return render_template('admin_edit_lot.html', lot=target_facility)

    @parking_app.route('/admin/facility/<int:facility_id>/spot-overview')
    @require_admin_access
    def facility_spot_overview(facility_id):
        target_facility = ParkingLot.query.get_or_404(facility_id)
        facility_spots = (
            ParkingSpot.query
            .filter_by(lot_id=target_facility.id)
            .order_by(ParkingSpot.id)
            .all()
        )

        detailed_spot_info = []
        for parking_spot in facility_spots:
            current_reservation = None
            if parking_spot.status == 'O':
                current_reservation = (
                    Reservation.query
                    .filter_by(spot_id=parking_spot.id, status='O')
                    .order_by(Reservation.parking_timestamp.desc())
                    .first()
                )
            detailed_spot_info.append({
                'spot': parking_spot, 
                'reservation': current_reservation
            })

        # Calculate summary statistics
        occupied_total = sum(1 for info in detailed_spot_info if info['spot'].status == 'O')
        available_total = target_facility.max_spots - occupied_total

        return render_template(
            'admin_spots.html',
            lot=target_facility,
            spot_info=detailed_spot_info,
            occupied=occupied_total,
            available=available_total
        )

    @parking_app.route('/admin/global-search', methods=['POST'])
    @require_admin_access
    def global_system_search():
        search_term = request.form.get('query', '').strip()
        if not search_term:
            flash('Please enter a search term.', 'warning')
            return redirect(url_for('admin_control_center'))

        # Search customers
        matching_customers = User.query.filter(
            (User.username.ilike(f'%{search_term}%')) |
            (User.email.ilike(f'%{search_term}%')) |
            (User.name.ilike(f'%{search_term}%'))
        ).all()

        # Search reservations by vehicle number
        vehicle_reservations = (
            Reservation.query
            .filter(Reservation.vehicle_number.ilike(f'%{search_term}%'))
            .order_by(Reservation.parking_timestamp.desc())
            .all()
        )

        # Search parking spots
        matching_spots = []
        if search_term.isdigit():  # Search by spot ID
            matching_spots = ParkingSpot.query.filter_by(id=int(search_term)).all()
        else:  # Search by facility name or postal code
            matching_spots = (
                ParkingSpot.query
                .join(ParkingLot)
                .filter(
                    (ParkingLot.prime_location_name.ilike(f'%{search_term}%')) |
                    (ParkingLot.pincode.ilike(f'%{search_term}%'))
                ).all()
            )

        return render_template(
            'admin_search_results.html',
            query=search_term,
            users=matching_customers,
            reservations=vehicle_reservations,
            spots=matching_spots
        )

    # ------------------------------------------------------------------
    # Customer Portal and Booking Routes
    # ------------------------------------------------------------------
    @parking_app.route('/customer/portal')
    @require_user_access
    def customer_portal():
        current_customer = User.query.filter_by(
            username=session['authenticated_user']).first()
        
        available_facilities = ParkingLot.query.all()
        for facility in available_facilities:
            facility.occupied_count = (
                ParkingSpot.query
                .filter_by(lot_id=facility.id, status='O')
                .count()
            )

        customer_bookings = (
            Reservation.query
            .filter_by(user_id=current_customer.id)
            .order_by(Reservation.parking_timestamp.desc())
            .all()
        )
        
        return render_template('user_dashboard.html',
                               user=current_customer,
                               lots=available_facilities,
                               reservations=customer_bookings)

    @parking_app.route('/customer/reserve-spot/<int:facility_id>', methods=['GET', 'POST'])
    @require_user_access
    def reserve_parking_spot(facility_id):
        current_customer = User.query.filter_by(username=session['authenticated_user']).first()
        available_spot = ParkingSpot.query.filter_by(lot_id=facility_id, status='A').first()

        if not available_spot:
            flash('No parking spots available at this location.', 'info')
            return redirect(url_for('customer_portal'))

        if request.method == 'POST':
            vehicle_registration = request.form['vehicle_number']
            estimated_departure = request.form.get('expected_end_time')

            departure_datetime = None
            if estimated_departure:
                departure_datetime = datetime.fromisoformat(estimated_departure)

            new_reservation = Reservation(
                user_id=current_customer.id,
                spot_id=available_spot.id,
                vehicle_number=vehicle_registration,
                parking_timestamp=datetime.utcnow(),
                expected_end_time=departure_datetime,
                parking_cost=0.0,
                payment_status='Pending',
                status='O'
            )
            
            db.session.add(new_reservation)
            available_spot.status = 'O'
            db.session.commit()
            flash('Parking spot reserved successfully.', 'success')
            return redirect(url_for('customer_portal'))

        return render_template('book_spot.html', lot_id=facility_id, spot_id=available_spot.id)

    @parking_app.route('/customer/checkout-spot/<int:spot_id>', methods=['GET', 'POST'])
    @require_user_access
    def checkout_parking_spot(spot_id):
        target_spot = ParkingSpot.query.get_or_404(spot_id)
        active_reservation = (
            Reservation.query
            .filter_by(spot_id=target_spot.id)
            .order_by(Reservation.parking_timestamp.desc())
            .first()
        )
        associated_facility = ParkingLot.query.get(target_spot.lot_id)

        if request.method == 'POST' and target_spot.status == 'O':
            payment_method = request.form.get('payment_mode')

            target_spot.status = 'A'
            active_reservation.leaving_timestamp = datetime.utcnow()
            
            # Calculate parking duration and cost
            parking_duration = (
                active_reservation.leaving_timestamp - active_reservation.parking_timestamp
            ).total_seconds() / 3600
            total_cost = round(parking_duration * associated_facility.price, 2)

            active_reservation.parking_cost = total_cost
            active_reservation.payment_status = 'Paid'
            active_reservation.payment_mode = payment_method
            active_reservation.payment_time = datetime.utcnow()
            active_reservation.status = 'A'
            
            db.session.commit()

            flash(f'Checkout completed. Total payment: ₹{total_cost} via {payment_method}', 'success')
            return redirect(url_for('customer_portal'))

        # Calculate estimated cost for display
        current_time = datetime.utcnow()
        estimated_cost = round(
            ((current_time - active_reservation.parking_timestamp).total_seconds() / 3600)
            * associated_facility.price, 2
        )
        
        return render_template('release_confirm.html', 
                              spot=target_spot, 
                              cost=estimated_cost, 
                              lot=associated_facility)

    @parking_app.route('/customer/find-facilities', methods=['GET', 'POST'])
    @require_user_access
    def find_parking_facilities():

        # Get current customer
        current_customer = User.query.filter_by(
            username=session['authenticated_user']).first()
        
        # Get customer's reservations
        customer_bookings = (
            Reservation.query
            .filter_by(user_id=current_customer.id)
            .order_by(Reservation.parking_timestamp.desc())
            .all()
        )
        
        matching_facilities = []
        search_query = ''
        
        if request.method == 'POST':
            search_query = request.form.get('query', '').strip()
            
            if search_query:
                matching_facilities = ParkingLot.query.filter(
                    (ParkingLot.prime_location_name.ilike(f'%{search_query}%')) |
                    (ParkingLot.address.ilike(f'%{search_query}%')) |
                    (ParkingLot.pincode.ilike(f'%{search_query}%'))
                ).all()
                
                # Calculate occupancy for each facility
                for facility in matching_facilities:
                    facility.occupied_count = (
                        ParkingSpot.query
                        .filter_by(lot_id=facility.id, status='O')
                        .count()
                    )
                
                if not matching_facilities:
                    flash(f'No facilities found matching "{search_query}". Showing all available facilities.', 'info')
                    # Show all facilities if no search results
                    matching_facilities = ParkingLot.query.all()
                    for facility in matching_facilities:
                        facility.occupied_count = (
                            ParkingSpot.query
                            .filter_by(lot_id=facility.id, status='O')
                            .count()
                        )
            else:
                flash('Please enter a search term.', 'warning')
                return redirect(url_for('customer_portal'))
        
        return render_template('user_dashboard.html',
                            user=current_customer,
                            lots=matching_facilities,
                            reservations=customer_bookings,
                            search_query=search_query)

    @parking_app.route('/customer/update-profile', methods=['GET', 'POST'])
    @require_user_access
    def update_customer_profile():
        current_customer = User.query.filter_by(username=session['authenticated_user']).first()
        
        if request.method == 'POST':
            current_customer.name = request.form['name']
            current_customer.address = request.form['address']
            current_customer.pincode = request.form['pincode']
            db.session.commit()
            flash('Profile information updated successfully.', 'success')
            return redirect(url_for('customer_portal'))

        return render_template('edit_profile.html', user=current_customer)

    @parking_app.route('/customer/personal-analytics')
    @require_user_access
    def customer_personal_analytics():
        current_customer = User.query.filter_by(username=session['authenticated_user']).first()

        # Retrieve all customer reservations
        all_customer_reservations = (
            Reservation.query
            .filter_by(user_id=current_customer.id)
            .order_by(Reservation.parking_timestamp.desc())
            .all()
        )

        # Analytics calculations
        expenditure_by_facility = {}
        visit_frequency_by_facility = {}
        total_expenditure = 0.0

        for reservation in all_customer_reservations:
            facility_name = reservation.spot.lot.prime_location_name
            reservation_cost = reservation.parking_cost or 0
            total_expenditure += reservation_cost

            expenditure_by_facility[facility_name] = expenditure_by_facility.get(facility_name, 0) + reservation_cost
            visit_frequency_by_facility[facility_name] = visit_frequency_by_facility.get(facility_name, 0) + 1

        # Format data for frontend visualization
        expenditure_chart_data = [{'name': facility, 'amount': cost}
                                 for facility, cost in expenditure_by_facility.items()]
        frequency_chart_data = [{'name': facility, 'count': visits}
                               for facility, visits in visit_frequency_by_facility.items()]

        return render_template(
            'user_summary.html',
            reservations=all_customer_reservations,
            total_spent=round(total_expenditure, 2),
            spending_chart_data=expenditure_chart_data,
            visit_chart_data=frequency_chart_data
        )

    # ------------------------------------------------------------------
    return parking_app

# ------------------------------------------------------------------
# Application Instance Creation
# ------------------------------------------------------------------
app = initialize_parking_app()

# ------------------------------------------------------------------
# Development Server Launch
# ------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5051, host='127.0.0.1')

