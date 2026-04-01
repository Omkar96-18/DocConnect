from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime 
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

print(f"DEBUG: DATABASE is {os.getenv('DATABASE')}")
print(f"DEBUG: USER is {os.getenv('USER')}")
# Don't print the actual password, just check if it exists
print(f"DEBUG: PASSWORD {os.getenv('PASSWORD')} LOADED: {os.getenv('PASSWORD') is not None}")

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("HOST"),
        database=os.getenv("DATABASE"),
        user=os.getenv("USER"),
        password=os.getenv("PASSWORD")
    )

def get_medical_centers():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT id, name FROM medical_centers')
    centers = cur.fetchall()
    cur.close()
    conn.close()
    return centers

@app.route('/register/patient', methods=['GET', 'POST'])
def register_patient():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        contact = request.form['contact']
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO patients (name, email, username, password_hash, contact_no) VALUES (%s, %s, %s, %s, %s)',
                        (name, email, username, password, contact))
            conn.commit()
            flash("Registration successful! Please login.")
            return redirect(url_for('login_patient'))
        except Exception as e:
            conn.rollback()
            flash("Error: Username or Email already exists.")
        finally:
            cur.close()
            conn.close()
    return render_template('register_patient.html')

@app.route('/login/patient', methods=['GET', 'POST'])
def login_patient():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM patients WHERE username = %s', (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['role'] = 'patient'
            return redirect(url_for('patient_dashboard'))
        else:
            flash("Invalid credentials")
    return render_template('login_patient.html')

@app.route('/register/doctor', methods=['GET', 'POST'])
def register_doctor():
    centers = get_medical_centers()
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        contact = request.form['contact_no']
        spec = request.form['specialization']
        exp = request.form['experience']
        license_no = request.form['license_no']
        center_id = request.form['medical_center_id']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO doctors (name, email, username, password_hash, contact_no, specialization, years_of_experience, license_no, medical_center_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, email, username, password, contact, spec, exp, license_no, center_id))
            conn.commit()
            flash("Doctor account created successfully!")
            return redirect(url_for('login_doctor'))
        except Exception as e:
            conn.rollback()
            flash(f"Error during registration: {str(e)}")
        finally:
            cur.close()
            conn.close()
            
    return render_template('register_doctor.html', centers=centers)

@app.route('/login/doctor', methods=['GET', 'POST'])
def login_doctor():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM doctors WHERE username = %s', (username,))
        doctor = cur.fetchone()
        cur.close()
        conn.close()

        if doctor and check_password_hash(doctor['password_hash'], password):
            session['user_id'] = doctor['id']
            session['role'] = 'doctor'
            session['name'] = doctor['name']
            return redirect(url_for('doctor_dashboard'))
        else:
            flash("Invalid doctor credentials.")

    return render_template('login_doctor.html')

@app.route('/logout')
def logout():
 
    session.clear()
    flash("You have been successfully logged out. Stay healthy!", "info")
    return redirect(url_for('login_patient'))


@app.route('/patient/my-appointments')
def patient_appointments():
    if session.get('role') != 'patient':
        return redirect(url_for('login_patient'))
    
    patient_id = session.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    

    cur.execute("""
        SELECT a.*, d.name as doctor_name 
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.patient_id = %s
        ORDER BY a.appointment_date DESC
    """, (patient_id,))
    
    appointments = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('patient_appointments.html', appointments=appointments)

@app.route('/doctor/dashboard')
def doctor_dashboard():
    if session.get('role') != 'doctor':
        return redirect(url_for('login_doctor'))
    
    doctor_id = session.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
    UPDATE appointments 
    SET status = 'expired' 
    WHERE appointment_date < NOW() AND status = 'pending'
    """)
    conn.commit()

    
    cur.execute("""
        SELECT a.*, p.name as patient_name, p.contact_no as patient_contact
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.doctor_id = %s
        ORDER BY a.appointment_date ASC
    """, (doctor_id,))
    
    appointments = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('doctor_dashboard.html', appointments=appointments)

@app.route('/appointment/update/<int:appointment_id>/<string:status>', methods=['POST'])
def update_appointment_status(appointment_id, status):
    if session.get('role') != 'doctor':
        flash("Unauthorized")
        return redirect(url_for('login_doctor'))
    

    if status not in ['approved', 'rejected']:
        flash("Invalid status")
        return redirect(url_for('doctor_dashboard'))

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE appointments SET status = %s WHERE id = %s AND doctor_id = %s", 
                    (status, appointment_id, session.get('user_id')))
        conn.commit()
        flash(f"Appointment {status} successfully!")
    except Exception as e:
        conn.rollback()
        flash("Update failed.")
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('doctor_dashboard'))

@app.route('/patient/dashboard')
def patient_dashboard():
    if session.get('role') != 'patient':
        return redirect(url_for('login_patient'))


    specialty = request.args.get('specialty', '')
    location = request.args.get('location', '')
    min_exp = request.args.get('experience', 0)

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)


    query = """
        SELECT d.*, mc.name as center_name, mc.address as center_location, mc.type as center_type
        FROM doctors d
        JOIN medical_centers mc ON d.medical_center_id = mc.id
        WHERE d.specialization ILIKE %s 
        AND mc.address ILIKE %s
        AND d.years_of_experience >= %s
    """
    
    cur.execute(query, (f'%{specialty}%', f'%{location}%', min_exp))
    doctors = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('patient_dashboard.html', doctors=doctors)


@app.route('/request_appointment', methods=['POST'])
def request_appointment():
    if session.get('role') != 'patient':
        flash("Only patients can book appointments.")
        return redirect(url_for('login_patient'))

    patient_id = session.get('user_id')
    doctor_id = request.form.get('doctor_id')
    appointment_date = request.form.get('appointment_time')

    if not appointment_date:
        flash("Please select a date and time.")
        return redirect(url_for('patient_dashboard'))

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO appointments (patient_id, doctor_id, appointment_date)
            VALUES (%s, %s, %s)
        """, (patient_id, doctor_id, appointment_date))
        conn.commit()
        flash("Appointment request sent! Waiting for doctor's approval.")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {str(e)}")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('patient_appointments'))

from datetime import datetime

@app.route('/patient/history')
def patient_history():
    if session.get('role') != 'patient':
        return redirect(url_for('login_patient'))
    
    patient_id = session.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
 
    cur.execute("""
        SELECT a.*, d.name as doctor_name, d.specialization, 
               mc.name as center_name, mc.address as center_address
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN medical_centers mc ON d.medical_center_id = mc.id
        WHERE a.patient_id = %s
        ORDER BY a.appointment_date DESC
    """, (patient_id,))
    
    appointments = cur.fetchall()
    cur.close()
    conn.close()
    

    now = datetime.now()
    
    return render_template('patient_history.html', 
                           appointments=appointments, 
                           now=now)


@app.route('/doctor/profile', methods=['GET', 'POST'])
def doctor_profile():
    if session.get('role') != 'doctor':
        return redirect(url_for('login_doctor'))
    
    doctor_id = session.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        name = request.form['name']
        specialization = request.form['specialization']
        contact = request.form['contact']
        
        cur.execute("""
            UPDATE doctors SET name = %s, specialization = %s, contact_no = %s 
            WHERE id = %s
        """, (name, specialization, contact, doctor_id))
        conn.commit()
        flash("Profile updated successfully!")

    cur.execute("SELECT * FROM doctors WHERE id = %s", (doctor_id,))
    doctor = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('doctor_profile.html', doctor=doctor)

@app.route('/doctor/patients')
def manage_patients():
    if 'user_id' not in session or session.get('role') != 'doctor':
        return redirect(url_for('index'))

    doctor_id = session['user_id']
    conn = get_db_connection()
    # Ensure you are using RealDictCursor so p.latest_appointment_id works in Jinja
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # This query joins patients with appointments to get the ID needed for the chat link
    cur.execute("""
        SELECT 
            p.id, 
            p.name, 
            p.blood_group, 
            p.contact_no, 
            MAX(a.id) as latest_appointment_id
        FROM patients p
        JOIN appointments a ON p.id = a.patient_id
        WHERE a.doctor_id = %s
        GROUP BY p.id, p.name, p.blood_group, p.contact_no
    """, (doctor_id,))
    
    patients = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('manage_patients.html', patients=patients)

@app.route('/doctor/patient/<int:patient_id>')
def patient_details(patient_id):
    if session.get('role') != 'doctor':
        flash("Access denied.")
        return redirect(url_for('login_doctor'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 1. Fetch full Patient Profile
    cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cur.fetchone()
    
    # 2. Fetch all appointments this patient has had (with any doctor, for full context)
    # Or keep it to just this doctor if privacy is a concern.
    cur.execute("""
        SELECT a.*, d.name as doctor_name 
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.patient_id = %s 
        ORDER BY a.appointment_date DESC
    """, (patient_id,))
    
    history = cur.fetchall()
    cur.close()
    conn.close()
    
    if not patient:
        flash("Patient not found.")
        return redirect(url_for('manage_patients'))
        
    return render_template('patient_details.html', patient=patient, history=history)

@app.route('/patient/profile', methods=['GET', 'POST'])
def patient_profile():
    if session.get('role') != 'patient':
        return redirect(url_for('login_patient'))
    
    patient_id = session.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        # Get data from form
        name = request.form['name']
        contact = request.form['contact_no']
        address = request.form['address']
        dob = request.form['date_of_birth'] or None
        blood = request.form['blood_group']
        allergies = request.form['allergies']
        med_history = request.form['medical_history']

        cur.execute("""
            UPDATE patients SET 
                name = %s, contact_no = %s, address = %s, 
                date_of_birth = %s, blood_group = %s, 
                allergies = %s, medical_history = %s 
            WHERE id = %s
        """, (name, contact, address, dob, blood, allergies, med_history, patient_id))
        
        conn.commit()
        flash("Profile updated successfully!")
        return redirect(url_for('patient_profile'))

    cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('patient_profile.html', patient=patient)



if __name__ == "__main__":
    app.run(debug=True)