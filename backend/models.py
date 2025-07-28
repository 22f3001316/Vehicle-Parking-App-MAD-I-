#Also Called DataBASE
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ------------------ USERS ------------------
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100))
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_type = db.Column(db.String(10), default='user')  # 'user' or 'admin'

    reservations = db.relationship('Reservation', backref='user', lazy=True)

# ------------------ ADMINS ------------------
class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(128))
    user_type = db.Column(db.String(10), default='admin')  # Only 'admin'

# ------------------ PARKING LOTS ------------------
class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    max_spots = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    spots = db.relationship('ParkingSpot', backref='lot', lazy=True, cascade="all, delete-orphan")

# ------------------ PARKING SPOTS ------------------
class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    status = db.Column(db.String(1), nullable=False, default='A')  # A = Available, O = Occupied

    reservations = db.relationship('Reservation', backref='spot', lazy=True)

# ------------------ RESERVATIONS ------------------
class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    vehicle_number = db.Column(db.String(20), nullable=False)
    parking_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    expected_end_time = db.Column(db.DateTime)
    leaving_timestamp = db.Column(db.DateTime)

    parking_cost = db.Column(db.Float)
    payment_status = db.Column(db.String(20))   # e.g., "Paid", "Pending"
    payment_mode = db.Column(db.String(20))     # e.g., "UPI", "Cash"
    payment_time = db.Column(db.DateTime)
    
    force_released = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(1), default='O')  # 'O' = Occupied, 'A' = Released

