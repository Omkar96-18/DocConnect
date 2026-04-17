-- Drop tables if they exist (Reverse order of dependency)
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS medical_centers;

-- i. Medical Centers
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

-- ii. Patients
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

-- iii. Doctors
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
);

-- iv. Appointments
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INTEGER REFERENCES doctors(id) ON DELETE CASCADE,
    appointment_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- v. Messages 
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    sender_role VARCHAR(10) NOT NULL,
    appointment_id INTEGER REFERENCES appointments(id) ON DELETE SET NULL,
    message_text TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO medical_centers (name, address, contact_no_1, type, description)
VALUES 
('City Central Hospital', '123 Health Ave, New York', '1234567890', 'General Hospital', 'Leading healthcare provider in the city.'),
('Green Valley Clinic', '456 Oak Lane, California', '2345678901', 'Clinic', 'Specializing in family medicine.'),
('St. Jude Childrens Center', '789 Maple Rd, Texas', '3456789012', 'Pediatric Hospital', 'Comprehensive care for children.'),
('Northside Dental Care', '101 Pine St, Washington', '4567890123', 'Dental Clinic', 'Quality dental services for all ages.'),
('Evergreen Wellness', '202 Birch Blvd, Oregon', '5678901234', 'Wellness Center', 'Holistic approach to health and fitness.'),
('Metro Eye Institute', '303 Cedar Dr, Florida', '6789012345', 'Eye Hospital', 'Advanced eye surgery and diagnostics.'),
('Summit Orthopedics', '404 Peak Way, Colorado', '7890123456', 'Specialized Hospital', 'Experts in bone and joint health.'),
('Lakeside Cardiology', '505 Shoreline Rd, Michigan', '8901234567', 'Specialized Hospital', 'Heart care and cardiovascular surgery.'),
('Downtown Urgent Care', '606 Broadway, Illinois', '9012345678', 'Urgent Care', 'Open 24/7 for medical emergencies.'),
('Pioneer Mental Health', '707 Frontier Ln, Arizona', '1122334455', 'Psychiatric Hospital', 'Compassionate mental health services.');