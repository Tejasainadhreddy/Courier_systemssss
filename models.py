from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Officer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    officer_name = db.Column(db.String(50), unique=True, nullable=False)
    off_pwd = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, default=2)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    member_since = db.Column(db.DateTime, default=datetime.utcnow)

class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_name = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.Text)
    manager = db.Column(db.String(100))

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    vehicle = db.Column(db.String(50))
    available = db.Column(db.Boolean, default=True)

class Courier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cons_no = db.Column(db.String(15), unique=True, nullable=False)
    ship_name = db.Column(db.String(100))
    rev_name = db.Column(db.String(100))
    ship_email = db.Column(db.String(100))
    rev_email = db.Column(db.String(100))
    ship_phone = db.Column(db.String(20))
    rev_phone = db.Column(db.String(20))
    ship_full_address = db.Column(db.Text)
    rev_full_address = db.Column(db.Text)
    special_instructions = db.Column(db.Text)      # ← NEW
    message_on_courier = db.Column(db.Text)        # ← NEW
    weight = db.Column(db.Float, default=1.0)
    p_type = db.Column(db.String(50)) 
    priority = db.Column(db.String(50)) 
    cost = db.Column(db.Float)
    est_delivery = db.Column(db.String(50))
    pick_date = db.Column(db.DateTime, default=datetime.utcnow)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=True)

class CourierTrack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cons_no = db.Column(db.String(15), db.ForeignKey('courier.cons_no'))
    status = db.Column(db.String(50)) 
    current_city = db.Column(db.String(100))
    comments = db.Column(db.Text)
    update_time = db.Column(db.DateTime, default=datetime.utcnow)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    subject = db.Column(db.String(100))
    message = db.Column(db.Text)
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)

class SupportQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Pending")