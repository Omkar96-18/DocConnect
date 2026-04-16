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
            flash("Error: Username or Email can be already exists.\n", e)
        finally:
            cur.close()
            conn.close()
    return render_template('register_patient.html')

@app.route('/', methods=['GET', 'POST'])
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
            session['username'] = user['username']
            session['name'] = user['name']
            session['email'] = user['email']
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
            session['username'] = doctor['username'] 
            session['email'] = doctor['email']
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

    cur.execute("SELECT COUNT(DISTINCT patient_id) FROM appointments WHERE doctor_id = %s AND status = 'approved'", (doctor_id,))
    total_patients = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(*) FROM appointments WHERE doctor_id = %s", (doctor_id,))
    total_queries = cur.fetchone()['count']
    
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
    return render_template('doctor_dashboard.html', 
                           appointments=appointments, 
                           total_patients=total_patients,
                           total_queries=total_queries)

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
        new_center_id = request.form.get('medical_center_id')
        name = request.form.get('name')
        specialization = request.form.get('specialization')
        contact = request.form.get('contact')
        experience = request.form.get('experience')
        
        try:
            # 2. Update the database including medical_center_id
            cur.execute("""
                UPDATE doctors 
                SET name = %s, specialization = %s, contact_no = %s, 
                    years_of_experience = %s,
                    medical_center_id = %s
                WHERE id = %s
            """, (name, specialization, contact, experience, new_center_id, doctor_id))
            conn.commit()
            
            session['name'] = name
            flash("Clinical Affiliation & Profile Synchronized!", "success")
        except Exception as e:
            conn.rollback()
            flash(f"System Error: {str(e)}", "error")

    cur.execute("SELECT * FROM doctors WHERE id = %s", (doctor_id,))
    doctor = cur.fetchone()

    cur.execute("SELECT id, name, type FROM medical_centers ORDER BY name ASC")
    centers = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('doctor_profile.html', doctor=doctor, centers=centers)

@app.route('/doctor/patients')
def manage_patients():
    if 'user_id' not in session or session.get('role') != 'doctor':
        return redirect(url_for('index'))

    doctor_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

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
    

    cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cur.fetchone()

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

@app.route('/messages')
def messages_list():
    if not session.get('user_id'):
        return redirect(url_for('login_patient'))
    
    user_id = session['user_id']
    role = session['role']
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

   
    if role == 'patient':
        
        query = """
            SELECT DISTINCT d.id, d.name, d.specialization as subtext
            FROM doctors d
            JOIN messages m ON (m.sender_id = d.id AND m.receiver_id = %s AND m.sender_role = 'doctor')
                            OR (m.receiver_id = d.id AND m.sender_id = %s AND m.sender_role = 'patient')
        """
    else:
        
        query = """
            SELECT DISTINCT p.id, p.name, p.blood_group as subtext
            FROM patients p
            JOIN messages m ON (m.sender_id = p.id AND m.receiver_id = %s AND m.sender_role = 'patient')
                            OR (m.receiver_id = p.id AND m.sender_id = %s AND m.sender_role = 'doctor')
        """
    
    cur.execute(query, (user_id, user_id))
    contacts = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('messages_list.html', contacts=contacts)

@app.route('/chat/<int:contact_id>')
def chat(contact_id):
    if not session.get('user_id'):
        return redirect(url_for('login_patient'))

    user_id = session['user_id']
    role = session['role']
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

   
    if role == 'patient':
        cur.execute("SELECT name FROM doctors WHERE id = %s", (contact_id,))
    else:
        cur.execute("SELECT name FROM patients WHERE id = %s", (contact_id,))
    recipient = cur.fetchone()

    
    cur.execute("""
        SELECT * FROM messages 
        WHERE (sender_id = %s AND receiver_id = %s AND sender_role = %s)
           OR (sender_id = %s AND receiver_id = %s AND sender_role != %s)
        ORDER BY created_at ASC
    """, (user_id, contact_id, role, contact_id, user_id, role))
    
    chat_history = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('chat.html', history=chat_history, recipient=recipient, contact_id=contact_id)

@app.route('/send_message/<int:receiver_id>', methods=['POST'])
def send_message(receiver_id):
    sender_id = session.get('user_id')
    role = session.get('role')
    text = request.form.get('message_text')

    if not text:
        return redirect(url_for('chat', contact_id=receiver_id))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO messages (sender_id, receiver_id, sender_role, message_text)
        VALUES (%s, %s, %s, %s)
    """, (sender_id, receiver_id, role, text))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('chat', contact_id=receiver_id))



if __name__ == "__main__":
    app.run(debug=True)