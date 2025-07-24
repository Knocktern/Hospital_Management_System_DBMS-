-- Hospital Management System Database Schema
-- Updated with Smart Enhancements: Email Notifications, Medical History, Prescriptions
-- SAFE: This will only affect the hospital_db database, not other databases

-- Create database if it doesn't exist and use it
CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;

-- Drop existing views first (to avoid conflicts)
DROP VIEW IF EXISTS patient_history;
DROP VIEW IF EXISTS doctor_schedule;
DROP VIEW IF EXISTS appointment_summary;

-- Drop existing tables if they exist (in correct order to handle foreign key constraints)
DROP TABLE IF EXISTS prescriptions;
DROP TABLE IF EXISTS medical_history;
DROP TABLE IF EXISTS appointment_requests;
DROP TABLE IF EXISTS trigr;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS test;

-- Test table (for database connection testing)
CREATE TABLE test (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(20) NOT NULL,
  email VARCHAR(20) NOT NULL
);

-- User table (base user authentication and management)
CREATE TABLE user (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  email VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(1000) NOT NULL,
  user_type ENUM('manager', 'doctor', 'patient') NOT NULL DEFAULT 'patient',
  phone VARCHAR(15),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Doctors table (doctor profiles and availability)
CREATE TABLE doctors (
  did INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  email VARCHAR(50) NOT NULL,
  doctorname VARCHAR(50) NOT NULL,
  dept VARCHAR(100) NOT NULL,
  specialization VARCHAR(100),
  qualification VARCHAR(200),
  experience_years INT DEFAULT 0,
  consultation_fee DECIMAL(10,2) DEFAULT 500.00,
  available_from TIME DEFAULT '09:00:00',
  available_to TIME DEFAULT '17:00:00',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Patients table (appointments and patient records)
CREATE TABLE patients (
  pid INT AUTO_INCREMENT PRIMARY KEY,
  patient_user_id INT,
  manager_user_id INT NOT NULL,
  doctor_id INT NOT NULL,
  email VARCHAR(50) NOT NULL,
  name VARCHAR(50) NOT NULL,
  gender VARCHAR(50) NOT NULL,
  age INT,
  slot VARCHAR(50) NOT NULL,
  disease VARCHAR(100) NOT NULL,
  appointment_time TIME NOT NULL,
  appointment_date DATE NOT NULL,
  dept VARCHAR(50) NOT NULL,
  number VARCHAR(15) NOT NULL,
  status ENUM('scheduled', 'completed', 'cancelled', 'no_show') DEFAULT 'scheduled',
  booking_type ENUM('manager_booking', 'patient_request') DEFAULT 'manager_booking',
  doctor_notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (patient_user_id) REFERENCES user(id) ON DELETE SET NULL,
  FOREIGN KEY (manager_user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (doctor_id) REFERENCES doctors(did) ON DELETE CASCADE
);

-- Appointment Requests table (patient appointment requests)
CREATE TABLE appointment_requests (
  request_id INT AUTO_INCREMENT PRIMARY KEY,
  patient_user_id INT NOT NULL,
  doctor_id INT NOT NULL,
  preferred_date DATE NOT NULL,
  preferred_time TIME NOT NULL,
  alternate_date DATE,
  alternate_time TIME,
  disease VARCHAR(100) NOT NULL,
  message TEXT,
  status ENUM('pending', 'approved', 'rejected', 'expired') DEFAULT 'pending',
  manager_response TEXT,
  responded_by INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  responded_at TIMESTAMP NULL,
  FOREIGN KEY (patient_user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (doctor_id) REFERENCES doctors(did) ON DELETE CASCADE,
  FOREIGN KEY (responded_by) REFERENCES user(id) ON DELETE SET NULL
);

-- Medical History table (patient medical records and visit history)
CREATE TABLE medical_history (
  history_id INT AUTO_INCREMENT PRIMARY KEY,
  patient_user_id INT NOT NULL,
  appointment_id INT NOT NULL,
  doctor_id INT NOT NULL,
  visit_date DATE NOT NULL,
  diagnosis TEXT,
  symptoms TEXT,
  treatment_given TEXT,
  follow_up_required BOOLEAN DEFAULT FALSE,
  follow_up_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (patient_user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (appointment_id) REFERENCES patients(pid) ON DELETE CASCADE,
  FOREIGN KEY (doctor_id) REFERENCES doctors(did) ON DELETE CASCADE
);

-- Prescriptions table (doctor prescriptions and medications)
CREATE TABLE prescriptions (
  prescription_id INT AUTO_INCREMENT PRIMARY KEY,
  appointment_id INT NOT NULL,
  doctor_id INT NOT NULL,
  patient_user_id INT NOT NULL,
  prescription_text TEXT NOT NULL,
  medications JSON,
  instructions TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (appointment_id) REFERENCES patients(pid) ON DELETE CASCADE,
  FOREIGN KEY (doctor_id) REFERENCES doctors(did) ON DELETE CASCADE,
  FOREIGN KEY (patient_user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Trigr table (audit trail and logging)
CREATE TABLE trigr (
  tid INT AUTO_INCREMENT PRIMARY KEY,
  pid INT,
  user_id INT,
  email VARCHAR(50) NOT NULL,
  name VARCHAR(50) NOT NULL,
  action VARCHAR(100) NOT NULL,
  details TEXT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL
);

-- Create indexes for better performance
CREATE INDEX idx_user_email ON user(email);
CREATE INDEX idx_user_type ON user(user_type);
CREATE INDEX idx_doctors_user_id ON doctors(user_id);
CREATE INDEX idx_doctors_dept ON doctors(dept);
CREATE INDEX idx_patients_doctor_id ON patients(doctor_id);
CREATE INDEX idx_patients_date ON patients(appointment_date);
CREATE INDEX idx_patients_status ON patients(status);
CREATE INDEX idx_patients_patient_user_id ON patients(patient_user_id);
CREATE INDEX idx_appointment_requests_patient ON appointment_requests(patient_user_id);
CREATE INDEX idx_appointment_requests_doctor ON appointment_requests(doctor_id);
CREATE INDEX idx_appointment_requests_status ON appointment_requests(status);
CREATE INDEX idx_medical_history_patient ON medical_history(patient_user_id);
CREATE INDEX idx_medical_history_doctor ON medical_history(doctor_id);
CREATE INDEX idx_medical_history_date ON medical_history(visit_date);
CREATE INDEX idx_prescriptions_patient ON prescriptions(patient_user_id);
CREATE INDEX idx_prescriptions_appointment ON prescriptions(appointment_id);
CREATE INDEX idx_prescriptions_doctor ON prescriptions(doctor_id);
CREATE INDEX idx_trigr_user_id ON trigr(user_id);
CREATE INDEX idx_trigr_timestamp ON trigr(timestamp);

-- Insert sample data for testing
INSERT INTO user (username, email, password, user_type, phone) VALUES
('Admin Manager', 'admin@hospital.com', 'pbkdf2:sha256:600000$salt$hash', 'manager', '1234567890'),
('Dr. John Smith', 'john.smith@hospital.com', 'pbkdf2:sha256:600000$salt$hash', 'doctor', '1234567891'),
('Dr. Sarah Johnson', 'sarah.johnson@hospital.com', 'pbkdf2:sha256:600000$salt$hash', 'doctor', '1234567892'),
('Patient User', 'patient@example.com', 'pbkdf2:sha256:600000$salt$hash', 'patient', '1234567893');

INSERT INTO doctors (user_id, email, doctorname, dept, specialization, qualification, experience_years, consultation_fee) VALUES
(2, 'john.smith@hospital.com', 'Dr. John Smith', 'Cardiology', 'Interventional Cardiology', 'MD, FACC', 10, 800.00),
(3, 'sarah.johnson@hospital.com', 'Dr. Sarah Johnson', 'Pediatrics', 'Child Development', 'MD, FAAP', 8, 600.00);

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS patient_insert_trigger;
DROP TRIGGER IF EXISTS patient_update_trigger;
DROP TRIGGER IF EXISTS patient_delete_trigger;
DROP TRIGGER IF EXISTS prescription_insert_trigger;

-- Create triggers for audit logging
DELIMITER //

CREATE TRIGGER patient_insert_trigger
AFTER INSERT ON patients
FOR EACH ROW
BEGIN
    INSERT INTO trigr (pid, user_id, email, name, action, details)
    VALUES (NEW.pid, NEW.manager_user_id, NEW.email, NEW.name, 'APPOINTMENT_CREATED', 
            CONCAT('Appointment created for ', NEW.name, ' with Dr. ID: ', NEW.doctor_id, ' on ', NEW.appointment_date));
END//

CREATE TRIGGER patient_update_trigger
AFTER UPDATE ON patients
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO trigr (pid, user_id, email, name, action, details)
        VALUES (NEW.pid, NEW.manager_user_id, NEW.email, NEW.name, 'APPOINTMENT_STATUS_CHANGED', 
                CONCAT('Appointment status changed from ', OLD.status, ' to ', NEW.status));
    END IF;
END//

CREATE TRIGGER patient_delete_trigger
AFTER DELETE ON patients
FOR EACH ROW
BEGIN
    INSERT INTO trigr (pid, user_id, email, name, action, details)
    VALUES (OLD.pid, OLD.manager_user_id, OLD.email, OLD.name, 'APPOINTMENT_DELETED', 
            CONCAT('Appointment deleted for ', OLD.name, ' scheduled on ', OLD.appointment_date));
END//

CREATE TRIGGER prescription_insert_trigger
AFTER INSERT ON prescriptions
FOR EACH ROW
BEGIN
    INSERT INTO trigr (pid, user_id, email, name, action, details)
    VALUES (NEW.appointment_id, NEW.doctor_id, 
            (SELECT email FROM user WHERE id = NEW.patient_user_id),
            (SELECT username FROM user WHERE id = NEW.patient_user_id),
            'PRESCRIPTION_ADDED', 
            CONCAT('Prescription added for appointment ID: ', NEW.appointment_id));
END//

DELIMITER ;

-- Create views for common queries (SAFE - will replace if exists)
CREATE OR REPLACE VIEW appointment_summary AS
SELECT 
    p.pid,
    p.name AS patient_name,
    p.email AS patient_email,
    p.appointment_date,
    p.appointment_time,
    p.status,
    d.doctorname,
    d.dept,
    u.username AS manager_name
FROM patients p
JOIN doctors d ON p.doctor_id = d.did
JOIN user u ON p.manager_user_id = u.id;

CREATE OR REPLACE VIEW doctor_schedule AS
SELECT 
    d.did,
    d.doctorname,
    d.dept,
    p.appointment_date,
    p.appointment_time,
    p.name AS patient_name,
    p.status
FROM doctors d
LEFT JOIN patients p ON d.did = p.doctor_id
WHERE p.appointment_date >= CURDATE()
ORDER BY d.did, p.appointment_date, p.appointment_time;

CREATE OR REPLACE VIEW patient_history AS
SELECT 
    mh.history_id,
    u.username AS patient_name,
    u.email AS patient_email,
    d.doctorname,
    d.dept,
    mh.visit_date,
    mh.diagnosis,
    mh.treatment_given,
    pr.prescription_text
FROM medical_history mh
JOIN user u ON mh.patient_user_id = u.id
JOIN doctors d ON mh.doctor_id = d.did
LEFT JOIN prescriptions pr ON mh.appointment_id = pr.appointment_id
ORDER BY mh.visit_date DESC;


SHOW TABLES;
