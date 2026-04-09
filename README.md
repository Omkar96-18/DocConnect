🏥 DocConnect - Project Setup Guide
This project is a Flask-based Medical Appointment System. It uses PostgreSQL as the primary database to handle secure patient and doctor records.

🗄️ Database Setup (PostgreSQL)
Follow these steps to recreate the database as defined in the project schema.

1. Create the Database
Open your terminal or psql shell and run:

SQL
CREATE DATABASE ai_doctordb;
2. Create Tables (Order Matters)
Because of Foreign Key constraints, you must create the tables in this specific order:

i. Medical Centers
```bash
CREATE TABLE medical_centers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    address TEXT NOT NULL,
    contact_no_1 TEXT NOT NULL CHECK (contact_no_1 ~ '^[0-9]{10,15}$'),
    contact_no_2 TEXT,
    description TEXT,
    type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
ii. Patients
```bash
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    contact_no TEXT NOT NULL CHECK (contact_no ~ '^[0-9]{10,15}$'),
    address TEXT,
    gender TEXT CHECK (gender IN ('male', 'female', 'other')),
    date_of_birth DATE,
    blood_group VARCHAR(5),
    allergies TEXT,
    medical_history TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
iii. Doctors
```bash
CREATE TABLE doctors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    contact_no TEXT NOT NULL CHECK (contact_no ~ '^[0-9]{10,15}$'),
    address TEXT,
    gender TEXT CHECK (gender IN ('male', 'female', 'other')),
    specialization VARCHAR(100) NOT NULL,
    years_of_experience INTEGER CHECK (years_of_experience >= 0),
    license_no VARCHAR(50) UNIQUE NOT NULL,
    medical_center_id INTEGER REFERENCES medical_centers(id) ON DELETE SET NULL,
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
iv. Appointments
```bash
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INTEGER REFERENCES doctors(id) ON DELETE CASCADE,
    appointment_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

v. Messages 
```bash
CREATE TABLE public.messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    sender_role VARCHAR(10) NOT NULL,
    appointment_id INTEGER,
    message_text TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraint
    CONSTRAINT messages_appointment_id_fkey 
        FOREIGN KEY (appointment_id) 
        REFERENCES appointments(id)
);
```
🚀 How to Run the Project
1. Clone & Environment
```bash
git clone <your-repo-link>
cd AIConsultationNAppointDoctor
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
2. Install Dependencies
Bash
pip install flask psycopg2-binary flask-sqlalchemy werkzeug
3. Configure Connection
Ensure your app.py or .env file matches your local PostgreSQL credentials:
```
