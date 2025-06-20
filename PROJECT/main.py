from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, logout_user, LoginManager, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail
from sqlalchemy import text, and_, or_
from datetime import datetime, timedelta, date, time
import json

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'sa'

# this is for getting unique user access
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# SMTP MAIL SERVER SETTINGS
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# SQLAlchemy DB connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/hospital_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Enhanced DB Models - Aligned with SQL Schema
class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(1000), nullable=False)
    user_type = db.Column(db.Enum('manager', 'doctor', 'patient'), nullable=False, default='patient')
    phone = db.Column(db.String(15))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

class Doctors(db.Model):
    did = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    doctorname = db.Column(db.String(50), nullable=False)
    dept = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100))
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer, default=0)
    consultation_fee = db.Column(db.Numeric(10, 2), default=500.00)
    available_from = db.Column(db.Time, default=time(9, 0))
    available_to = db.Column(db.Time, default=time(17, 0))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

class Patients(db.Model):
    pid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # NULL if booked by manager
    manager_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Manager who created booking
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.did'), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer)
    slot = db.Column(db.String(50), nullable=False)
    disease = db.Column(db.String(100), nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    dept = db.Column(db.String(50), nullable=False)
    number = db.Column(db.String(15), nullable=False)
    status = db.Column(db.Enum('scheduled', 'completed', 'cancelled', 'no_show'), default='scheduled')
    booking_type = db.Column(db.Enum('manager_booking', 'patient_request'), default='manager_booking')
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

class AppointmentRequests(db.Model):
    __tablename__ = 'appointment_requests'
    
    request_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.did'), nullable=False)
    preferred_date = db.Column(db.Date, nullable=False)
    preferred_time = db.Column(db.Time, nullable=False)
    alternate_date = db.Column(db.Date)
    alternate_time = db.Column(db.Time)
    disease = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.Enum('pending', 'approved', 'rejected', 'expired'), default='pending')
    manager_response = db.Column(db.Text)
    responded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    responded_at = db.Column(db.TIMESTAMP, nullable=True)

class Trigr(db.Model):
    tid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pid = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    email = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.TIMESTAMP, default=datetime.utcnow)

# Helper Functions
def check_time_conflict(doctor_id, appointment_date, appointment_time, exclude_pid=None):
    """Check if the requested time slot conflicts with existing appointments"""
    try:
        # Convert string inputs to proper types if necessary
        if isinstance(appointment_date, str):
            appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        if isinstance(appointment_time, str):
            appointment_time = datetime.strptime(appointment_time, '%H:%M').time()
        
        # Build query to check existing appointments
        query = """
        SELECT appointment_time FROM patients 
        WHERE doctor_id = :doctor_id AND appointment_date = :appointment_date 
        AND status IN ('scheduled', 'completed')
        """
        params = {"doctor_id": doctor_id, "appointment_date": appointment_date}
        
        if exclude_pid:
            query += " AND pid != :exclude_pid"
            params["exclude_pid"] = exclude_pid
            
        existing_appointments = db.session.execute(text(query), params).fetchall()
        
        # Check for direct time conflicts (assuming 30-minute slots)
        appointment_datetime = datetime.combine(appointment_date, appointment_time)
        appointment_end = appointment_datetime + timedelta(minutes=30)
        
        for existing in existing_appointments:
            existing_datetime = datetime.combine(appointment_date, existing.appointment_time)
            existing_end = existing_datetime + timedelta(minutes=30)
            
            # Check for overlap
            if (appointment_datetime < existing_end and appointment_end > existing_datetime):
                return True, f"Time slot conflicts with existing appointment at {existing.appointment_time}"
                
        return False, "Time slot is available"
    except Exception as e:
        return True, f"Error checking time conflict: {str(e)}"

def get_available_slots(doctor_id, appointment_date):
    """Get available time slots for a doctor on a specific date"""
    try:
        doctor = Doctors.query.get(doctor_id)
        if not doctor:
            return []
            
        # Convert string date if necessary
        if isinstance(appointment_date, str):
            appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            
        start_time = datetime.combine(appointment_date, doctor.available_from)
        end_time = datetime.combine(appointment_date, doctor.available_to)
        
        # Generate 30-minute slots
        slots = []
        current_time = start_time
        
        while current_time < end_time:
            time_obj = current_time.time()
            conflict, _ = check_time_conflict(doctor_id, appointment_date, time_obj)
            
            if not conflict:
                slots.append(time_obj.strftime('%H:%M'))
                
            current_time += timedelta(minutes=30)
            
        return slots
    except Exception as e:
        return []

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/doctors', methods=['POST', 'GET'])
@login_required
def doctors():
    if current_user.user_type not in ['manager']:
        flash("Access denied. Only managers can add doctors.", "danger")
        return redirect(url_for('index'))
        
    if request.method == "POST":
        email = request.form.get('email')
        doctorname = request.form.get('doctorname')
        dept = request.form.get('dept')
        specialization = request.form.get('specialization', '')
        qualification = request.form.get('qualification', '')
        experience_years = request.form.get('experience_years', 0)
        consultation_fee = request.form.get('consultation_fee', 500.00)
        available_from = request.form.get('available_from', '09:00')
        available_to = request.form.get('available_to', '17:00')
        
        # Check if doctor email already exists
        existing_doctor = Doctors.query.filter_by(email=email).first()
        if existing_doctor:
            flash("Doctor with this email already exists", "warning")
            return render_template('doctor.html')
        
        # Check if user exists with this email and is a doctor
        user = User.query.filter_by(email=email, user_type='doctor').first()
        if not user:
            flash("Please create a user account with type 'doctor' first", "warning")
            return render_template('doctor.html')
            
        try:
            new_doctor = Doctors(
                user_id=user.id,
                email=email,
                doctorname=doctorname,
                dept=dept,
                specialization=specialization,
                qualification=qualification,
                experience_years=int(experience_years) if experience_years else 0,
                consultation_fee=float(consultation_fee) if consultation_fee else 500.00,
                available_from=datetime.strptime(available_from, '%H:%M').time(),
                available_to=datetime.strptime(available_to, '%H:%M').time()
            )
            db.session.add(new_doctor)
            db.session.commit()
            flash("Doctor Information Stored Successfully", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding doctor: {str(e)}", "danger")
            
    return render_template('doctor.html')

@app.route('/patients', methods=['POST', 'GET'])
@login_required
def patient():
    if current_user.user_type != 'manager':
        flash("Access denied. Only managers can book appointments.", "danger")
        return redirect(url_for('index'))
        
    doctors_list = Doctors.query.all()
    
    if request.method == "POST":
        doctor_id = request.form.get('doctor_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        
        # Convert string inputs to proper types
        try:
            appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            appointment_time_obj = datetime.strptime(appointment_time, '%H:%M').time()
        except ValueError:
            flash("Invalid date or time format", "danger")
            return render_template('patient.html', doctors=doctors_list)
        
        # Check for time conflicts
        conflict, message = check_time_conflict(doctor_id, appointment_date_obj, appointment_time_obj)
        if conflict:
            flash(f"Booking failed: {message}", "danger")
            return render_template('patient.html', doctors=doctors_list)
        
        # Get patient user if email provided matches a user
        patient_email = request.form.get('email')
        patient_user = User.query.filter_by(email=patient_email, user_type='patient').first()
        
        # Determine slot based on time
        hour = appointment_time_obj.hour
        if hour < 12:
            slot = 'morning'
        elif hour < 17:
            slot = 'afternoon'
        else:
            slot = 'evening'
            
        try:
            new_appointment = Patients(
                patient_user_id=patient_user.id if patient_user else None,
                manager_user_id=current_user.id,
                doctor_id=int(doctor_id),
                email=patient_email,
                name=request.form.get('name'),
                gender=request.form.get('gender'),
                age=int(request.form.get('age')) if request.form.get('age') else None,
                slot=slot,
                disease=request.form.get('disease'),
                appointment_time=appointment_time_obj,
                appointment_date=appointment_date_obj,
                dept=request.form.get('dept'),
                number=request.form.get('number'),
                status='scheduled',
                booking_type='manager_booking'
            )
            db.session.add(new_appointment)
            db.session.commit()
            flash("Appointment Booked Successfully", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error booking appointment: {str(e)}", "danger")
        
    return render_template('patient.html', doctors=doctors_list)

@app.route('/check_availability', methods=['POST'])
@login_required
def check_availability():
    """AJAX endpoint to check available time slots"""
    doctor_id = request.json.get('doctor_id')
    appointment_date = request.json.get('date')
    
    if not doctor_id or not appointment_date:
        return jsonify({'error': 'Missing doctor_id or date'}), 400
        
    available_slots = get_available_slots(doctor_id, appointment_date)
    return jsonify({'available_slots': available_slots})

@app.route('/bookings')
@login_required
def bookings():
    if current_user.user_type == 'manager':
        # Manager sees all bookings they created
        appointments = Patients.query.filter_by(manager_user_id=current_user.id).all()
    elif current_user.user_type == 'doctor':
        # Doctor sees their own appointments
        doctor = Doctors.query.filter_by(user_id=current_user.id).first()
        if doctor:
            appointments = Patients.query.filter_by(doctor_id=doctor.did).all()
        else:
            appointments = []
    elif current_user.user_type == 'patient':
        # Patient sees their own appointments
        appointments = Patients.query.filter_by(patient_user_id=current_user.id).all()
    else:
        appointments = []
        
    return render_template('booking.html', query=appointments)
@app.route("/edit/<string:pid>", methods=['POST', 'GET'])
@login_required
def edit(pid):
    appointment = Patients.query.filter_by(pid=pid).first()
    
    if not appointment:
        flash("Appointment not found", "danger")
        return redirect('/bookings')
        
    # Check permissions
    if current_user.user_type == 'manager' and appointment.manager_user_id != current_user.id:
        flash("Access denied", "danger")
        return redirect('/bookings')
    elif current_user.user_type == 'doctor':
        doctor = Doctors.query.filter_by(user_id=current_user.id).first()
        if not doctor or appointment.doctor_id != doctor.did:
            flash("Access denied", "danger")
            return redirect('/bookings')
    elif current_user.user_type == 'patient' and appointment.patient_user_id != current_user.id:
        flash("Access denied", "danger")
        return redirect('/bookings')
    
    # Get all doctors for the dropdown
    doctors_list = Doctors.query.all()
    
    if request.method == "POST":
        doctor_id = request.form.get('doctor_id', appointment.doctor_id)
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        
        try:
            appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            appointment_time_obj = datetime.strptime(appointment_time, '%H:%M').time()
        except ValueError:
            flash("Invalid date or time format", "danger")
            return render_template('edit.html', posts=appointment, doctors=doctors_list, today=date.today())
        
        # Check for time conflicts (excluding current appointment)
        conflict, message = check_time_conflict(doctor_id, appointment_date_obj, appointment_time_obj, exclude_pid=pid)
        if conflict:
            flash(f"Update failed: {message}", "danger")
            return render_template('edit.html', posts=appointment, doctors=doctors_list, today=date.today())
        
        try:
            # Update appointment
            appointment.doctor_id = int(doctor_id)
            appointment.email = request.form.get('email')
            appointment.name = request.form.get('name')
            appointment.gender = request.form.get('gender')
            appointment.age = int(request.form.get('age')) if request.form.get('age') else None
            appointment.disease = request.form.get('disease')
            appointment.appointment_time = appointment_time_obj
            appointment.appointment_date = appointment_date_obj
            appointment.dept = request.form.get('dept')
            appointment.number = request.form.get('number')
            
            # Update slot based on time
            hour = appointment_time_obj.hour
            if hour < 12:
                appointment.slot = 'morning'
            elif hour < 17:
                appointment.slot = 'afternoon'
            else:
                appointment.slot = 'evening'
            
            db.session.commit()
            flash("Appointment Updated Successfully", "success")
            return redirect('/bookings')
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating appointment: {str(e)}", "danger")
            
    return render_template('edit.html', posts=appointment, doctors=doctors_list, today=date.today())
# @app.route("/edit/<string:pid>", methods=['POST', 'GET'])
# @login_required
# def edit(pid):
#     appointment = Patients.query.filter_by(pid=pid).first()
    
#     if not appointment:
#         flash("Appointment not found", "danger")
#         return redirect('/bookings')
        
#     # Check permissions
#     if current_user.user_type == 'manager' and appointment.manager_user_id != current_user.id:
#         flash("Access denied", "danger")
#         return redirect('/bookings')
#     elif current_user.user_type == 'doctor':
#         doctor = Doctors.query.filter_by(user_id=current_user.id).first()
#         if not doctor or appointment.doctor_id != doctor.did:
#             flash("Access denied", "danger")
#             return redirect('/bookings')
#     elif current_user.user_type == 'patient' and appointment.patient_user_id != current_user.id:
#         flash("Access denied", "danger")
#         return redirect('/bookings')
    
#     if request.method == "POST":
#         doctor_id = request.form.get('doctor_id', appointment.doctor_id)
#         appointment_date = request.form.get('appointment_date')
#         appointment_time = request.form.get('appointment_time')
        
#         try:
#             appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
#             appointment_time_obj = datetime.strptime(appointment_time, '%H:%M').time()
#         except ValueError:
#             flash("Invalid date or time format", "danger")
#             return render_template('edit.html', posts=appointment)
        
#         # Check for time conflicts (excluding current appointment)
#         conflict, message = check_time_conflict(doctor_id, appointment_date_obj, appointment_time_obj, exclude_pid=pid)
#         if conflict:
#             flash(f"Update failed: {message}", "danger")
#             return render_template('edit.html', posts=appointment)
        
#         try:
#             # Update appointment
#             appointment.doctor_id = int(doctor_id)
#             appointment.email = request.form.get('email')
#             appointment.name = request.form.get('name')
#             appointment.gender = request.form.get('gender')
#             appointment.age = int(request.form.get('age')) if request.form.get('age') else None
#             appointment.disease = request.form.get('disease')
#             appointment.appointment_time = appointment_time_obj
#             appointment.appointment_date = appointment_date_obj
#             appointment.dept = request.form.get('dept')
#             appointment.number = request.form.get('number')
            
#             # Update slot based on time
#             hour = appointment_time_obj.hour
#             if hour < 12:
#                 appointment.slot = 'morning'
#             elif hour < 17:
#                 appointment.slot = 'afternoon'
#             else:
#                 appointment.slot = 'evening'
            
#             db.session.commit()
#             flash("Appointment Updated Successfully", "success")
#             return redirect('/bookings')
#         except Exception as e:
#             db.session.rollback()
#             flash(f"Error updating appointment: {str(e)}", "danger")
            
#     return render_template('edit.html', posts=appointment)

@app.route("/delete/<string:pid>", methods=['POST', 'GET'])
@login_required
def delete(pid):
    appointment = Patients.query.filter_by(pid=pid).first()
    
    if not appointment:
        flash("Appointment not found", "danger")
        return redirect('/bookings')
        
    # Check permissions
    if current_user.user_type == 'manager' and appointment.manager_user_id != current_user.id:
        flash("Access denied", "danger")
        return redirect('/bookings')
    elif current_user.user_type == 'doctor':
        doctor = Doctors.query.filter_by(user_id=current_user.id).first()
        if not doctor or appointment.doctor_id != doctor.did:
            flash("Access denied", "danger")
            return redirect('/bookings')
    elif current_user.user_type == 'patient' and appointment.patient_user_id != current_user.id:
        flash("Access denied", "danger")
        return redirect('/bookings')
            
    try:
        db.session.delete(appointment)
        db.session.commit()
        flash("Appointment Deleted Successfully", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting appointment: {str(e)}", "danger")
        
    return redirect('/bookings')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')  # Remove default value to catch missing selections
        phone = request.form.get('phone')
        
        # Debug: Print form data
        print(f"DEBUG: Signup form data - user_type: {user_type}, email: {email}")
        
        # Validation
        if not username or not email or not password:
            flash("Username, email, and password are required", "danger")
            return render_template('signup.html')
            
        if not user_type or user_type not in ['patient', 'doctor', 'manager']:
            flash("Please select a valid user type", "danger")
            return render_template('signup.html')
        
        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email Already Exists", "warning")
            return render_template('signup.html')
            
        try:
            encpassword = generate_password_hash(password)
            new_user = User(
                username=username, 
                email=email, 
                password=encpassword, 
                user_type=user_type,  # This should now capture the correct value
                phone=phone
            )
            db.session.add(new_user)
            db.session.commit()
            
            print(f"DEBUG: User created successfully with user_type: {user_type}")
            
            flash(f"Signup Successful as {user_type.title()}. Please Login", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print(f"DEBUG: Error creating user: {str(e)}")
            flash(f"Error creating user: {str(e)}", "danger")
            
    return render_template('signup.html')
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            
            # Debug: Print user type to console
            print(f"DEBUG: User {user.email} logged in with user_type: {user.user_type}")
            
            flash(f"Login Successful - Welcome {user.user_type.title()}", "success")
            
            # Redirect based on user_type
            if user.user_type == 'doctor':
                print("DEBUG: Redirecting to doctor_dashboard")
                return redirect(url_for('doctor_dashboard'))
            elif user.user_type == 'patient':
                print("DEBUG: Redirecting to patient_dashboard")
                return redirect(url_for('patient_dashboard'))
            elif user.user_type == 'manager':
                print("DEBUG: Redirecting to manager_dashboard")
                return redirect(url_for('index'))
            else:
                print(f"DEBUG: Unknown user_type: {user.user_type}, redirecting to index")
                return redirect(url_for('index'))
        else:
            flash("Invalid Credentials", "danger")
            
    return render_template('login.html')
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout Successful", "warning")
    return redirect(url_for('login'))

@app.route('/doctor_dashboard')
@login_required
def doctor_dashboard():
    if current_user.user_type != 'doctor':
        flash("Access denied", "danger")
        return redirect(url_for('index'))
        
    doctor = Doctors.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash("Doctor record not found", "danger")
        return redirect(url_for('index'))
        
    # Get today's appointments
    today = date.today()
    todays_appointments = Patients.query.filter_by(
        doctor_id=doctor.did, 
        appointment_date=today
    ).filter(Patients.status != 'cancelled').order_by(Patients.appointment_time).all()
    
    # Get all appointments
    all_appointments = Patients.query.filter_by(
        doctor_id=doctor.did
    ).filter(Patients.status != 'cancelled').order_by(
        Patients.appointment_date, Patients.appointment_time
    ).all()
    
    return render_template('doctor_dashboard.html', 
                         doctor=doctor, 
                         todays_appointments=todays_appointments,
                         all_appointments=all_appointments)

@app.route('/patient_dashboard')
@login_required
def patient_dashboard():
    if current_user.user_type != 'patient':
        flash("Access denied", "danger")
        return redirect(url_for('index'))
        
    # Get patient's appointments
    appointments = Patients.query.filter_by(
        patient_user_id=current_user.id
    ).order_by(Patients.appointment_date, Patients.appointment_time).all()
    
    # Get available doctors
    doctors_list = Doctors.query.all()
    
    # Get pending appointment requests
    requests = AppointmentRequests.query.filter_by(
        patient_user_id=current_user.id
    ).order_by(AppointmentRequests.created_at.desc()).all()
    
    return render_template('patient_dashboard.html', 
                         appointments=appointments, 
                         doctors=doctors_list,
                         requests=requests)

@app.route('/request_appointment', methods=['POST'])
@login_required
def request_appointment():
    if current_user.user_type != 'patient':
        flash("Access denied", "danger")
        return redirect(url_for('index'))
        
    doctor_id = request.form.get('doctor_id')
    preferred_date = request.form.get('preferred_date')
    preferred_time = request.form.get('preferred_time')
    disease = request.form.get('disease')
    message = request.form.get('message', '')
    
    try:
        preferred_date_obj = datetime.strptime(preferred_date, '%Y-%m-%d').date()
        preferred_time_obj = datetime.strptime(preferred_time, '%H:%M').time()
        
        # Check if slot is available
        conflict, conflict_message = check_time_conflict(doctor_id, preferred_date_obj, preferred_time_obj)
        if conflict:
            flash(f"Request failed: {conflict_message}", "danger")
            return redirect(url_for('patient_dashboard'))
        
        # Create appointment request
        new_request = AppointmentRequests(
            patient_user_id=current_user.id,
            doctor_id=int(doctor_id),
            preferred_date=preferred_date_obj,
            preferred_time=preferred_time_obj,
            disease=disease,
            message=message
        )
        db.session.add(new_request)
        db.session.commit()
        
        flash("Appointment request sent successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating request: {str(e)}", "danger")
        
    return redirect(url_for('patient_dashboard'))

@app.route('/manage_requests')
@login_required
def manage_requests():
    if current_user.user_type != 'manager':
        flash("Access denied", "danger")
        return redirect(url_for('index'))
        
    # Get pending appointment requests with related data
    requests = db.session.query(
        AppointmentRequests,
        User.username.label('patient_name'),
        User.email.label('patient_email'),
        Doctors.doctorname,
        Doctors.dept
    ).join(
        User, AppointmentRequests.patient_user_id == User.id
    ).join(
        Doctors, AppointmentRequests.doctor_id == Doctors.did
    ).filter(
        AppointmentRequests.status == 'pending'
    ).order_by(AppointmentRequests.created_at).all()
    
    return render_template('manage_requests.html', requests=requests)

@app.route('/approve_request/<int:request_id>')
@login_required
def approve_request(request_id):
    if current_user.user_type != 'manager':
        flash("Access denied", "danger")
        return redirect(url_for('index'))
    
    appointment_request = AppointmentRequests.query.get(request_id)
    if not appointment_request:
        flash("Request not found", "danger")
        return redirect(url_for('manage_requests'))
    
    # Check if slot is still available
    conflict, message = check_time_conflict(
        appointment_request.doctor_id, 
        appointment_request.preferred_date, 
        appointment_request.preferred_time
    )
    
    if conflict:
        flash(f"Cannot approve: {message}", "danger")
        return redirect(url_for('manage_requests'))
    
    try:
        # Get patient and doctor details
        patient = User.query.get(appointment_request.patient_user_id)
        doctor = Doctors.query.get(appointment_request.doctor_id)
        
        # Determine slot based on time
        hour = appointment_request.preferred_time.hour
        if hour < 12:
            slot = 'morning'
        elif hour < 17:
            slot = 'afternoon'
        else:
            slot = 'evening'
        
        # Create the appointment
        new_appointment = Patients(
            patient_user_id=patient.id,
            manager_user_id=current_user.id,
            doctor_id=appointment_request.doctor_id,
            email=patient.email,
            name=patient.username,
            gender='Not specified',  # You might want to add this to user model
            slot=slot,
            disease=appointment_request.disease,
            appointment_time=appointment_request.preferred_time,
            appointment_date=appointment_request.preferred_date,
            dept=doctor.dept,
            number=patient.phone or '',
            status='scheduled',
            booking_type='patient_request'
        )
        
        db.session.add(new_appointment)
        
        # Update request status
        appointment_request.status = 'approved'
        appointment_request.responded_by = current_user.id
        appointment_request.responded_at = datetime.utcnow()
        
        db.session.commit()
        flash("Appointment approved successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error approving request: {str(e)}", "danger")
        
    return redirect(url_for('manage_requests'))

@app.route('/reject_request/<int:request_id>')
@login_required
def reject_request(request_id):
    if current_user.user_type != 'manager':
        flash("Access denied", "danger")
        return redirect(url_for('index'))
    
    appointment_request = AppointmentRequests.query.get(request_id)
    if not appointment_request:
        flash("Request not found", "danger")
        return redirect(url_for('manage_requests'))
    

    appointment_request.status = 'rejected'
    appointment_request.manager_id = current_user.id
    db.session.commit()
    
    flash("Appointment request rejected", "warning")
    return redirect(url_for('manage_requests'))

@app.route('/test')
def test():
    try:
        Test.query.all()
        return 'My database is Connected'
    except:
        return 'My db is not Connected'

@app.route('/details')
@login_required
def details():
    posts = db.session.execute(text("SELECT * FROM trigr")).fetchall()
    return render_template('trigers.html', posts=posts)

@app.route('/search', methods=['POST', 'GET'])
@login_required
def search():
    if request.method == "POST":
        query = request.form.get('search')
        name = Doctors.query.filter_by(doctorname=query).first()
        if name:
            flash("Doctor is Available", "info")
        else:
            flash("Doctor is Not Available", "danger")
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)