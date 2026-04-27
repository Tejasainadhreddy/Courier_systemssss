from app import app, db
from models import Officer, User, Branch, Driver, Courier, CourierTrack
from datetime import datetime

with app.app_context():
    db.create_all()
    
    # ==================== SUPER ADMIN ====================
    if not Officer.query.filter_by(officer_name='Team_7').first():
        db.session.add(Officer(officer_name='Team_7', off_pwd='password7', level=1))
        print("✅ Super Admin created")

    # ==================== SAMPLE CUSTOMER ====================
    if not User.query.filter_by(email='sriram@csueb.edu').first():
        u = User(
            fullname='Sriram Kumar',
            email='sriram@csueb.edu',
            password='password123',
            phone='510-885-3000',
            address='25800 Carlos Bee Blvd, Hayward, CA'
        )
        db.session.add(u)
        print("✅ Sample Customer created")

    # ==================== BRANCHES ====================
    if not Branch.query.first():
        db.session.add(Branch(branch_name='Hayward Hub', location='25800 Carlos Bee Blvd, Hayward, CA', manager='Alice Johnson'))
        db.session.add(Branch(branch_name='Oakland Depot', location='1000 Broadway, Oakland, CA', manager='Bob Smith'))
        print("✅ Branches seeded")

    # ==================== DRIVERS ====================
    if not Driver.query.first():
        db.session.add(Driver(driver_name='Mike Rodriguez', password='driver123', phone='510-123-4567', vehicle='Van T7-01', available=True))
        db.session.add(Driver(driver_name='Sarah Patel', password='driver456', phone='510-987-6543', vehicle='Truck T7-02', available=True))
        db.session.add(Driver(driver_name='David Kim', password='driver789', phone='510-555-1212', vehicle='Van T7-03', available=True))
        print("✅ Drivers seeded")

    # ==================== SAMPLE COURIERS (Updated with new fields) ====================
    if not Courier.query.first():
        # Sample for Mike Rodriguez
        c1 = Courier(
            cons_no="T7-XYZ789",
            ship_name="Sriram Kumar",
            rev_name="Rahul Sharma",
            ship_email="sriram@csueb.edu",
            rev_email="rahul.sharma@gmail.com",
            ship_phone="510-885-3000",
            rev_phone="415-987-6543",
            ship_full_address="25800 Carlos Bee Blvd, Hayward, CA",
            rev_full_address="123 Market Street, San Francisco, CA",
            weight=2.5,
            p_type="Box",
            priority="Express",
            cost=35.0,
            est_delivery="Out for Delivery",
            driver_id=1
        )
        db.session.add(c1)
        db.session.add(CourierTrack(cons_no="T7-XYZ789", status="Pickup Requested", current_city="Hayward"))
        db.session.add(CourierTrack(cons_no="T7-XYZ789", status="Reached Hub", current_city="Hayward Hub"))
        db.session.add(CourierTrack(cons_no="T7-XYZ789", status="Out for Delivery", current_city="San Francisco"))

        # Sample for Sarah Patel
        c2 = Courier(
            cons_no="T7-ABC123",
            ship_name="Priya Patel",
            rev_name="John Lee",
            ship_email="priya.patel@gmail.com",
            rev_email="john.lee@yahoo.com",
            ship_phone="510-222-3333",
            rev_phone="510-444-5555",
            ship_full_address="Hayward, CA",
            rev_full_address="Oakland, CA",
            weight=1.8,
            p_type="Envelope",
            priority="Standard",
            cost=18.0,
            est_delivery="In Transit",
            driver_id=2
        )
        db.session.add(c2)
        db.session.add(CourierTrack(cons_no="T7-ABC123", status="In Transit", current_city="Oakland Hub"))

        print("✅ Sample Couriers seeded with new fields")

    db.session.commit()
    print("\n🎉 DATABASE RESET COMPLETE!")
    print("   Admin     → Team_7 / password7")
    print("   Customer  → sriram@csueb.edu / password123")
    print("   Drivers   → Mike Rodriguez / driver123, Sarah Patel / driver456")