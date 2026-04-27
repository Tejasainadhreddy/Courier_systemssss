from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Courier, CourierTrack, Officer, User, ContactMessage, Branch, Driver, SupportQuery
from models import Officer, User, Branch, Driver, Courier, CourierTrack, SupportQuery
import random, string
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///team7_logistics.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'team7_master_engineering_key_2026'
db.init_app(app)

def gen_id():
    return f"T7-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

def calculate_cost(weight, priority):
    base_fee = 10.0
    rate_per_kg = 8.0
    priority_fee = 15.0 if priority == "Express" else 0.0
    return round(base_fee + (weight * rate_per_kg) + priority_fee, 2)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if it's an Admin/Officer
        admin = Officer.query.filter_by(officer_name=username, off_pwd=password).first()
        if admin:
            session.clear()
            session.update({'user': admin.officer_name, 'role': 'admin', 'level': admin.level})
            return redirect(url_for('admin_dashboard'))
        
        # Check if it's a regular Customer/User
        user = User.query.filter_by(email=username, password=password).first()
        if user:
            session.clear()
            session.update({'user': user.fullname, 'role': 'user', 'id': user.id})
            return redirect(url_for('user_dashboard'))
        
        # Check if it's a Driver
        driver = Driver.query.filter_by(driver_name=username, password=password).first()
        if driver:
            session.clear()
            session.update({'user': driver.driver_name, 'role': 'driver', 'id': driver.id})
            return redirect(url_for('driver_dashboard'))
        
        flash("Invalid Credentials", "danger")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_user = User(fullname=request.form.get('fullname'), 
                        email=request.form.get('email'),
                        password=request.form.get('password'), 
                        phone=request.form.get('phone'), 
                        address=request.form.get('address'))
        db.session.add(new_user)
        db.session.commit()
        flash("Registration Successful! Please Login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash("Admin access required", "danger")
        return redirect(url_for('login'))

    search = request.args.get('search', '')

    # Query all couriers with search functionality
    if search:
        couriers = Courier.query.filter(
            db.or_(
                Courier.cons_no.ilike(f'%{search}%'),
                Courier.ship_name.ilike(f'%{search}%'),
                Courier.rev_name.ilike(f'%{search}%'),
                Courier.est_delivery.ilike(f'%{search}%')
            )
        ).all()
    else:
        couriers = Courier.query.all()

    u_count = User.query.count()
    t_orders = Courier.query.count()

    # Add assigned driver name for display
    for c in couriers:
        if c.driver_id:
            driver = Driver.query.get(c.driver_id)
            c.assigned_driver = driver.driver_name if driver else "Not Assigned"
        else:
            c.assigned_driver = "Not Assigned"

    return render_template('admin_dashboard.html', 
                           couriers=couriers, 
                           u_count=u_count, 
                           t_orders=t_orders,
                           search=search)

@app.route('/admin-analytics')
def admin_analytics():
    if session.get('role') != 'admin':
        flash("Admin access required", "danger")
        return redirect(url_for('login'))
    total_revenue = sum(c.cost for c in Courier.query.all())
    total_shipments = Courier.query.count()
    pending = Courier.query.filter(Courier.est_delivery.like('%Awaiting%') | 
                                   Courier.est_delivery.like('%In Transit%')).count()
    delivered = Courier.query.filter_by(est_delivery='Delivered').count()
    return render_template('admin_analytics.html',
                           total_revenue=total_revenue,
                           total_shipments=total_shipments,
                           pending=pending,
                           delivered=delivered)

@app.route('/user_dashboard')
def user_dashboard():
    if session.get('role') != 'user':
        flash("Please login as a customer to access dashboard", "danger")
        return redirect(url_for('login'))
    
    user_id = session.get('id')
    if not user_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if not user:
        flash("User not found. Please login again.", "danger")
        return redirect(url_for('login'))
    
    orders = Courier.query.filter(
        (Courier.ship_name == user.fullname) | 
        (Courier.rev_name == user.fullname)
    ).all()
    
    # Add cancel eligibility safely
    now = datetime.utcnow()
    for o in orders:
        o.can_cancel = (o.pick_date > (now - timedelta(minutes=30)))
    
    return render_template('user_dashboard.html', user=user, orders=orders)
    
@app.route('/update-profile', methods=['POST'])
def update_profile():
    if session.get('role') != 'user':
        return redirect(url_for('login'))
    u = User.query.get(session['id'])
    u.fullname = request.form.get('fullname')
    u.phone = request.form.get('phone')
    u.address = request.form.get('address')
    db.session.commit()
    flash("Profile Updated Successfully!", "success")
    return redirect(url_for('user_dashboard'))

# ==================== CHANGE PASSWORD ====================
@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if session.get('role') != 'user':
        flash("Please login as customer", "danger")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        old_pwd = request.form.get('old_password')
        new_pwd = request.form.get('new_password')
        confirm_pwd = request.form.get('confirm_password')
        
        user = User.query.get(session['id'])
        if not user:
            flash("User not found", "danger")
            return redirect(url_for('login'))
        
        if user.password != old_pwd:
            flash("Old password is incorrect", "danger")
        elif new_pwd != confirm_pwd:
            flash("New passwords do not match", "danger")
        elif not new_pwd:
            flash("New password cannot be empty", "danger")
        else:
            user.password = new_pwd
            db.session.commit()
            flash("Password changed successfully!", "success")
            return redirect(url_for('user_dashboard'))
    
    return render_template('change_password.html')

# ==================== CANCEL ORDER (within 30 minutes) ====================
@app.route('/cancel-order/<cons_no>')
def cancel_order(cons_no):
    if session.get('role') != 'user':
        flash("Please login as customer", "danger")
        return redirect(url_for('login'))
    courier = Courier.query.filter_by(cons_no=cons_no).first()
    if not courier:
        flash("Order not found", "danger")
        return redirect(url_for('user_dashboard'))
    # Check if created within last 30 minutes
    time_limit = datetime.utcnow() - timedelta(minutes=55730)
    if courier.pick_date < time_limit:
        flash("You can only cancel orders within 30 minutes of creation.", "danger")
        return redirect(url_for('user_dashboard'))
    # Delete related tracks and courier
    CourierTrack.query.filter_by(cons_no=cons_no).delete()
    db.session.delete(courier)
    db.session.commit()
    flash(f"Order {cons_no} cancelled successfully.", "success")
    return redirect(url_for('user_dashboard'))

#===================== REQUEST PICKUP ====================
@app.route('/request-pickup', methods=['GET', 'POST'])
def request_pickup():
    if session.get('role') != 'user':
        flash("Please login as a customer", "danger")
        return redirect(url_for('login'))
    
    u = User.query.get(session['id'])
    if request.method == 'POST':
        cid = gen_id()
        weight = float(request.form.get('weight'))
        priority = request.form.get('priority')
        cost = calculate_cost(weight, priority)
        
        new_c = Courier(
            cons_no=cid, 
            ship_name=u.fullname, 
            rev_name=request.form.get('rev_name'),
            ship_email=u.email,
            rev_email=request.form.get('rev_email'),
            ship_phone=u.phone,
            rev_phone=request.form.get('rev_phone'),
            ship_full_address=u.address,
            rev_full_address=request.form.get('rev_full_address'),
            special_instructions=request.form.get('special_instructions'),
            message_on_courier=request.form.get('message_on_courier'),
            weight=weight,
            p_type=request.form.get('p_type'), 
            priority=priority, 
            cost=cost, 
            est_delivery="Awaiting Approval"
        )
        db.session.add(new_c)
        db.session.add(CourierTrack(cons_no=cid, status="Pickup Requested", current_city=u.address))
        db.session.commit()
        
        flash(f"Pickup Requested Successfully! Tracking ID: {cid} | Cost: ${cost:.2f}", "success")
        return redirect(url_for('user_dashboard'))
    
    return render_template('request_pickup.html', user=u)

@app.route('/add-courier', methods=['GET', 'POST'])
def add_courier():
    if session.get('role') != 'admin':
        flash("Admin access required", "danger")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        cid = gen_id()
        weight = float(request.form.get('weight'))
        priority = request.form.get('priority')
        cost = calculate_cost(weight, priority)
        
        new_c = Courier(
            cons_no=cid, 
            ship_name=request.form.get('ship_name'), 
            rev_name=request.form.get('rev_name'),
            ship_email=request.form.get('ship_email'),
            rev_email=request.form.get('rev_email'),
            ship_phone=request.form.get('ship_phone'),
            rev_phone=request.form.get('rev_phone'),
            ship_full_address=request.form.get('ship_full_address'),
            rev_full_address=request.form.get('rev_full_address'),
            special_instructions=request.form.get('special_instructions'),
            message_on_courier=request.form.get('message_on_courier'),
            weight=weight, 
            p_type=request.form.get('p_type'), 
            priority=priority, 
            cost=cost, 
            est_delivery="Awaiting Approval"
        )
        db.session.add(new_c)
        db.session.add(CourierTrack(cons_no=cid, status="Pickup Requested", current_city=request.form.get('ship_full_address')))
        db.session.commit()
        
        flash(f"Shipment Created! Tracking ID: {cid} | Cost: ${cost:.2f}", "success")
        return render_template('add_courier.html', success_id=cid)
    
    return render_template('add_courier.html')

# (All other routes like update-status, mark-delivered, track-search, track_details, receipt, branches, drivers, create-admin, assign-driver, logout remain exactly the same as previous full version)

@app.route('/update-status', methods=['GET', 'POST'])
def update_status():
    if session.get('role') != 'admin':
        flash("Admin access required", "danger")
        return redirect(url_for('login'))
    
    cons_no = request.args.get('cons_no', '')
    
    if request.method == 'POST':
        cid = request.form.get('cons_no')
        status = request.form.get('status')
        city = request.form.get('city')
        reason = request.form.get('reason')
        comments = request.form.get('comments')
        
        c = Courier.query.filter_by(cons_no=cid).first()
        if c:
            # Combine reason with comments if Delayed
            final_comments = comments or ''
            if status == 'Delayed' and reason:
                final_comments = f"Delay Reason: {reason}. {final_comments}"
            
            new_track = CourierTrack(
                cons_no=cid,
                status=status,
                current_city=city,
                comments=final_comments.strip()
            )
            db.session.add(new_track)
            c.est_delivery = status
            db.session.commit()
            
            flash(f"Shipment {cid} updated to {status} successfully!", "success")
            return redirect(url_for('admin_dashboard'))
        
        flash("Courier not found!", "danger")
    
    return render_template('update_status.html', cons_no=cons_no)

@app.route('/mark-delivered/<cons_no>')
def mark_delivered(cons_no):
    if session.get('role') != 'admin':
        flash("Admin access required", "danger")
        return redirect(url_for('login'))
    c = Courier.query.filter_by(cons_no=cons_no).first()
    if c:
        c.est_delivery = "Delivered"
        db.session.add(CourierTrack(cons_no=cons_no, status="Delivered", 
                                    current_city="Destination", comments="Successfully delivered"))
        db.session.commit()
        flash(f"Shipment {cons_no} marked as Delivered!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/track-search', methods=['POST'])
def track_search():
    cid = request.form.get('cons_no')
    c = Courier.query.filter_by(cons_no=cid).first()
    t = CourierTrack.query.filter_by(cons_no=cid).order_by(CourierTrack.update_time.desc()).first()
    if c and t:
        return render_template('home.html', track_result=t, courier_result=c)
    flash("Tracking ID not found.", "danger")
    return redirect(url_for('home'))

@app.route('/track/<cons_no>')
def track_details(cons_no):
    courier = Courier.query.filter_by(cons_no=cons_no).first()
    if not courier:
        flash("Tracking ID not found.", "danger")
        return redirect(url_for('home'))
    tracks = CourierTrack.query.filter_by(cons_no=cons_no).order_by(CourierTrack.update_time.desc()).all()
    driver_name = "Not Assigned"
    if courier.driver_id:
        driver = Driver.query.get(courier.driver_id)
        driver_name = driver.driver_name if driver else "Not Assigned"
    return render_template('track_details.html', courier=courier, tracks=tracks, driver_name=driver_name)

@app.route('/receipt/<cons_no>')
def receipt(cons_no):
    courier = Courier.query.filter_by(cons_no=cons_no).first()
    if not courier:
        flash("Receipt not found.", "danger")
        return redirect(url_for('home'))
    tracks = CourierTrack.query.filter_by(cons_no=cons_no).order_by(CourierTrack.update_time.desc()).all()
    driver_name = "Not Assigned"
    if courier.driver_id:
        driver = Driver.query.get(courier.driver_id)
        driver_name = driver.driver_name if driver else "Not Assigned"
    return render_template('receipt.html', courier=courier, tracks=tracks, driver_name=driver_name)

@app.route('/about', methods=['GET', 'POST'])
def about():
    if request.method == 'POST':
        db.session.add(ContactMessage(name=request.form.get('name'),
                                      email=request.form.get('email'),
                                      subject=request.form.get('subject'),
                                      message=request.form.get('message')))
        db.session.commit()
        flash("Support Ticket Created. We will get back to you soon!", "success")
        return redirect(url_for('home'))
    return render_template('about.html')

@app.route('/customer-care')
def customer_care():
    return render_template('customer_care.html')

@app.route('/services')
def services():
    return render_template('services_page.html')

@app.route('/branches', methods=['GET', 'POST'])
def branches():
    if session.get('role') != 'admin':
        flash("Admin access required", "danger")
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form.get('branch_name')
        loc = request.form.get('location')
        mgr = request.form.get('manager')
        if name:
            new_branch = Branch(branch_name=name, location=loc, manager=mgr)
            db.session.add(new_branch)
            db.session.commit()
            flash("New Hub added successfully!", "success")
        return redirect(url_for('branches'))
    branches_list = Branch.query.all()
    return render_template('branches.html', branches=branches_list)

@app.route('/delete-branch/<int:branch_id>')
def delete_branch(branch_id):
    if session.get('role') != 'admin':
        flash("Admin access required", "danger")
        return redirect(url_for('login'))
    branch = Branch.query.get_or_404(branch_id)
    db.session.delete(branch)
    db.session.commit()
    flash("Hub deleted successfully!", "success")
    return redirect(url_for('branches'))

@app.route('/drivers', methods=['GET', 'POST'])
def drivers():
    if session.get('role') != 'admin':
        flash("Admin access required", "danger")
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form.get('driver_name')
        phone = request.form.get('phone')
        vehicle = request.form.get('vehicle')
        if name:
            new_driver = Driver(driver_name=name, phone=phone, vehicle=vehicle, available=True)
            db.session.add(new_driver)
            db.session.commit()
            flash("New Driver added successfully!", "success")
        return redirect(url_for('drivers'))
    drivers_list = Driver.query.all()
    return render_template('drivers.html', drivers=drivers_list)

@app.route('/delete-driver/<int:driver_id>')
def delete_driver(driver_id):
    if session.get('role') != 'admin':
        flash("Admin access required", "danger")
        return redirect(url_for('login'))
    driver = Driver.query.get_or_404(driver_id)
    db.session.delete(driver)
    db.session.commit()
    flash("Driver deleted successfully!", "success")
    return redirect(url_for('drivers'))

@app.route('/create-admin', methods=['GET', 'POST'])
def create_admin():
    if session.get('role') != 'admin' or session.get('level') != 1:
        flash("Super Admin access required", "danger")
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if Officer.query.filter_by(officer_name=username).first():
            flash("Admin username already exists", "danger")
        else:
            new_admin = Officer(officer_name=username, off_pwd=password, level=2)
            db.session.add(new_admin)
            db.session.commit()
            flash("New Admin created successfully!", "success")
            return redirect(url_for('admin_dashboard'))
    return render_template('create_admin.html')

@app.route('/assign-driver/<cons_no>', methods=['GET', 'POST'])
def assign_driver(cons_no):
    if session.get('role') != 'admin':
        flash("Admin access required", "danger")
        return redirect(url_for('login'))
    courier = Courier.query.filter_by(cons_no=cons_no).first()
    if not courier:
        flash("Courier not found", "danger")
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        driver_id = request.form.get('driver_id')
        if driver_id:
            courier.driver_id = int(driver_id)
            db.session.add(CourierTrack(cons_no=cons_no, status="Driver Assigned", 
                                        current_city="Hub", comments="Driver assigned to parcel"))
            db.session.commit()
            flash("Driver assigned successfully!", "success")
            return redirect(url_for('admin_dashboard'))
    drivers = Driver.query.filter_by(available=True).all()
    return render_template('assign_driver.html', courier=courier, drivers=drivers)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

# ==================== DRIVER LOGIN & DASHBOARD ====================
@app.route('/driver-login', methods=['GET', 'POST'])
def driver_login():
    if request.method == 'POST':
        name = request.form.get('driver_name')
        pwd = request.form.get('password')
        driver = Driver.query.filter_by(driver_name=name, password=pwd).first()
        if driver:
            session.clear()
            session.update({'user': driver.driver_name, 'role': 'driver', 'id': driver.id})
            return redirect(url_for('driver_dashboard'))
        flash("Invalid Driver Credentials", "danger")
    return render_template('driver_login.html')

@app.route('/driver-dashboard')
def driver_dashboard():
    if session.get('role') != 'driver':
        flash("Driver access required. Please login as driver.", "danger")
        return redirect(url_for('login'))
    
    driver_id = session.get('id')
    assigned_parcels = Courier.query.filter_by(driver_id=driver_id).all()
    
    return render_template('driver_dashboard.html', 
                           parcels=assigned_parcels, 
                           driver_name=session.get('user'))

@app.route('/driver-mark-delivered/<cons_no>')
def driver_mark_delivered(cons_no):
    if session.get('role') != 'driver':
        flash("Driver access required", "danger")
        return redirect(url_for('login'))
    
    courier = Courier.query.filter_by(cons_no=cons_no, driver_id=session.get('id')).first()
    if courier:
        courier.est_delivery = "Delivered"
        db.session.add(CourierTrack(cons_no=cons_no, status="Delivered", current_city="Destination", comments="Delivered by driver"))
        db.session.commit()
        flash(f"Parcel {cons_no} marked as Delivered!", "success")
    else:
        flash("You can only update parcels assigned to you.", "danger")
    return redirect(url_for('driver_dashboard'))

@app.route('/driver-logout')
def driver_logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

# Handle Support Query Submission
@app.route('/about', methods=['POST'])
def submit_support():
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')

    if name and email and message:
        new_query = SupportQuery(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        db.session.add(new_query)
        db.session.commit()
        flash("Your support query has been submitted successfully!", "success")
    else:
        flash("Please fill all required fields.", "danger")

    return redirect(url_for('about'))

# Admin View All Support Queries
@app.route('/support-queries')
def support_queries():
    if session.get('role') != 'admin':
        flash("Admin access required", "danger")
        return redirect(url_for('login'))
    
    queries = SupportQuery.query.order_by(SupportQuery.date_submitted.desc()).all()
    return render_template('support_queries.html', queries=queries)


if __name__ == '__main__':
    app.run(debug=True, port=5001)