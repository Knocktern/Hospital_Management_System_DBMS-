-- Enhanced Hospital Management System Database Schema

-- Drop existing tables if they exist (optional - for clean setup)
DROP TABLE IF EXISTS appointment_requests;
DROP TABLE IF EXISTS trigr;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS test;

-- Create enhanced user table with user types
CREATE TABLE user (
  id int(11) NOT NULL AUTO_INCREMENT,
  username varchar(50) NOT NULL,
  email varchar(50) NOT NULL UNIQUE,
  password varchar(1000) NOT NULL,
  user_type ENUM('manager', 'doctor', 'patient') NOT NULL DEFAULT 'patient',
  phone varchar(15),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
);

-- Enhanced doctors table with more details
CREATE TABLE doctors (
  did int(11) NOT NULL AUTO_INCREMENT,
  user_id int(11) NOT NULL,
  email varchar(50) NOT NULL,
  doctorname varchar(50) NOT NULL,
  dept varchar(100) NOT NULL,
  specialization varchar(100),
  qualification varchar(200),
  experience_years int(2) DEFAULT 0,
  consultation_fee decimal(10,2) DEFAULT 500.00,
  available_from TIME DEFAULT '09:00:00',
  available_to TIME DEFAULT '17:00:00',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (did),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Enhanced patients table with appointment slots
CREATE TABLE patients (
  pid int(11) NOT NULL AUTO_INCREMENT,
  patient_user_id int(11) NULL, -- NULL if booked by manager, otherwise patient's user_id
  manager_user_id int(11) NOT NULL, -- Manager who created the booking
  doctor_id int(11) NOT NULL,
  email varchar(50) NOT NULL,
  name varchar(50) NOT NULL,
  gender varchar(50) NOT NULL,
  age int(3),
  slot varchar(50) NOT NULL,
  disease varchar(100) NOT NULL,
  appointment_time TIME NOT NULL,
  appointment_date DATE NOT NULL,
  dept varchar(50) NOT NULL,
  number varchar(15) NOT NULL,
  status ENUM('scheduled', 'completed', 'cancelled', 'no_show') DEFAULT 'scheduled',
  booking_type ENUM('manager_booking', 'patient_request') DEFAULT 'manager_booking',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (pid),
  FOREIGN KEY (patient_user_id) REFERENCES user(id) ON DELETE SET NULL,
  FOREIGN KEY (manager_user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (doctor_id) REFERENCES doctors(did) ON DELETE CASCADE,
  UNIQUE KEY unique_doctor_datetime (doctor_id, appointment_date, appointment_time)
);

-- New table for appointment requests from patients
CREATE TABLE appointment_requests (
  request_id int(11) NOT NULL AUTO_INCREMENT,
  patient_user_id int(11) NOT NULL,
  doctor_id int(11) NOT NULL,
  preferred_date DATE NOT NULL,
  preferred_time TIME NOT NULL,
  alternate_date DATE,
  alternate_time TIME,
  disease varchar(100) NOT NULL,
  message TEXT,
  status ENUM('pending', 'approved', 'rejected', 'expired') DEFAULT 'pending',
  manager_response TEXT,
  responded_by int(11),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  responded_at TIMESTAMP NULL,
  PRIMARY KEY (request_id),
  FOREIGN KEY (patient_user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (doctor_id) REFERENCES doctors(did) ON DELETE CASCADE,
  FOREIGN KEY (responded_by) REFERENCES user(id) ON DELETE SET NULL
);

-- Enhanced triggers table
CREATE TABLE trigr (
  tid int(11) NOT NULL AUTO_INCREMENT,
  pid int(11),
  user_id int(11),
  email varchar(50) NOT NULL,
  name varchar(50) NOT NULL,
  action varchar(100) NOT NULL,
  details TEXT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (tid),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL
);

-- Test table (keep as is for database connectivity testing)
CREATE TABLE test (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(20) NOT NULL,
  email varchar(20) NOT NULL,
  PRIMARY KEY (id)
);

-- Insert sample data

-- Insert users (managers, doctors, patients)
INSERT INTO user (username, email, password, user_type, phone) VALUES
('admin_manager', 'manager@hms.com', 'pbkdf2:sha256:260000$dummy$hash1', 'manager', '9999999999'),
('dr_anil', 'anil@gmail.com', 'pbkdf2:sha256:260000$dummy$hash2', 'doctor', '9988776655'),
('dr_deepa', 'deepa@gmail.com', 'pbkdf2:sha256:260000$dummy$hash3', 'doctor', '9988776656'),
('dr_rajesh', 'rajesh@gmail.com', 'pbkdf2:sha256:260000$dummy$hash4', 'doctor', '9988776657'),
('dr_seema', 'seema@gmail.com', 'pbkdf2:sha256:260000$dummy$hash5', 'doctor', '9988776658'),
('patient_rohit', 'rohit1@gmail.com', 'pbkdf2:sha256:260000$dummy$hash6', 'patient', '9123456789'),
('patient_rita', 'rita@gmail.com', 'pbkdf2:sha256:260000$dummy$hash7', 'patient', '9234567890'),
('patient_amit', 'amit@gmail.com', 'pbkdf2:sha256:260000$dummy$hash8', 'patient', '9345678901'),
('patient_rekha', 'rekha@gmail.com', 'pbkdf2:sha256:260000$dummy$hash9', 'patient', '9456789012');

-- Insert doctors
INSERT INTO doctors (user_id, email, doctorname, dept, specialization, qualification, experience_years, consultation_fee, available_from, available_to) VALUES
(2, 'anil@gmail.com', 'Dr. Anil Mehra', 'Neurology', 'Brain Surgery', 'MBBS, MD Neurology', 10, 1500.00, '09:00:00', '17:00:00'),
(3, 'deepa@gmail.com', 'Dr. Deepa Kaur', 'Pediatrics', 'Child Care', 'MBBS, MD Pediatrics', 8, 800.00, '10:00:00', '18:00:00'),
(4, 'rajesh@gmail.com', 'Dr. Rajesh Patel', 'Orthopedics', 'Bone Surgery', 'MBBS, MS Orthopedics', 12, 1200.00, '08:00:00', '16:00:00'),
(5, 'seema@gmail.com', 'Dr. Seema Rani', 'Psychiatry', 'Mental Health', 'MBBS, MD Psychiatry', 6, 1000.00, '11:00:00', '19:00:00');

-- Insert sample appointments
INSERT INTO patients (patient_user_id, manager_user_id, doctor_id, email, name, gender, age, slot, disease, appointment_time, appointment_date, dept, number, status, booking_type) VALUES
(6, 1, 1, 'rohit1@gmail.com', 'Rohit Sharma', 'Male', 28, 'morning', 'Headache and dizziness', '09:00:00', '2025-06-20', 'Neurology', '9123456789', 'scheduled', 'manager_booking'),
(7, 1, 2, 'rita@gmail.com', 'Rita Paul', 'Female', 25, 'afternoon', 'Child fever', '14:00:00', '2025-06-21', 'Pediatrics', '9234567890', 'scheduled', 'manager_booking'),
(8, 1, 3, 'amit@gmail.com', 'Amit Joshi', 'Male', 35, 'evening', 'Knee pain', '15:30:00', '2025-06-22', 'Orthopedics', '9345678901', 'scheduled', 'manager_booking');

-- Insert sample appointment requests
INSERT INTO appointment_requests (patient_user_id, doctor_id, preferred_date, preferred_time, disease, message, status) VALUES
(9, 4, '2025-06-23', '12:00:00', 'Anxiety and stress', 'I need urgent consultation for anxiety issues', 'pending'),
(6, 2, '2025-06-24', '11:00:00', 'Regular checkup', 'Routine health checkup needed', 'pending');

-- Insert test data
INSERT INTO test (name, email) VALUES
('Test User', 'test@hms.com'),
('Sample User', 'sample@hms.com');

-- Create enhanced triggers

DELIMITER $$

-- Trigger for patient insertion
CREATE TRIGGER patientinsertion 
AFTER INSERT ON patients
FOR EACH ROW
BEGIN
    INSERT INTO trigr (pid, user_id, email, name, action, details) 
    VALUES (NEW.pid, NEW.manager_user_id, NEW.email, NEW.name, 'APPOINTMENT SCHEDULED', 
            CONCAT('Appointment scheduled for ', NEW.appointment_date, ' at ', NEW.appointment_time, ' with doctor ID: ', NEW.doctor_id));
END$$

-- Trigger for patient update
CREATE TRIGGER PatientUpdate 
AFTER UPDATE ON patients
FOR EACH ROW
BEGIN
    INSERT INTO trigr (pid, user_id, email, name, action, details) 
    VALUES (NEW.pid, NEW.manager_user_id, NEW.email, NEW.name, 'APPOINTMENT UPDATED', 
            CONCAT('Appointment updated from ', OLD.appointment_date, ' ', OLD.appointment_time, ' to ', NEW.appointment_date, ' ', NEW.appointment_time));
END$$

-- Trigger for patient deletion
CREATE TRIGGER PatientDelete 
BEFORE DELETE ON patients
FOR EACH ROW
BEGIN
    INSERT INTO trigr (pid, user_id, email, name, action, details) 
    VALUES (OLD.pid, OLD.manager_user_id, OLD.email, OLD.name, 'APPOINTMENT CANCELLED', 
            CONCAT('Appointment cancelled for ', OLD.appointment_date, ' at ', OLD.appointment_time));
END$$

-- Trigger for appointment request insertion
CREATE TRIGGER appointment_request_created
AFTER INSERT ON appointment_requests
FOR EACH ROW
BEGIN
    DECLARE patient_name VARCHAR(50);
    DECLARE patient_email VARCHAR(50);
    
    SELECT username, email INTO patient_name, patient_email 
    FROM user WHERE id = NEW.patient_user_id;
    
    INSERT INTO trigr (user_id, email, name, action, details) 
    VALUES (NEW.patient_user_id, patient_email, patient_name, 'APPOINTMENT REQUEST CREATED', 
            CONCAT('Patient requested appointment for ', NEW.preferred_date, ' at ', NEW.preferred_time));
END$$

DELIMITER ;

-- Create indexes for better performance
CREATE INDEX idx_patients_doctor_date ON patients(doctor_id, appointment_date);
CREATE INDEX idx_patients_manager ON patients(manager_user_id);
CREATE INDEX idx_patients_patient ON patients(patient_user_id);
CREATE INDEX idx_appointment_requests_patient ON appointment_requests(patient_user_id);
CREATE INDEX idx_appointment_requests_doctor ON appointment_requests(doctor_id);
CREATE INDEX idx_doctors_dept ON doctors(dept);
CREATE INDEX idx_user_type ON user(user_type);

-- Create view for doctor schedules
CREATE VIEW doctor_schedule AS
SELECT 
    d.did,
    d.doctorname,
    d.dept,
    d.available_from,
    d.available_to,
    p.appointment_date,
    p.appointment_time,
    p.name as patient_name,
    p.status
FROM doctors d
LEFT JOIN patients p ON d.did = p.doctor_id
ORDER BY d.did, p.appointment_date, p.appointment_time;

-- Create view for manager dashboard
CREATE VIEW manager_dashboard AS
SELECT 
    COUNT(CASE WHEN p.appointment_date = CURDATE() THEN 1 END) as today_appointments,
    COUNT(CASE WHEN p.appointment_date > CURDATE() THEN 1 END) as upcoming_appointments,
    COUNT(CASE WHEN p.status = 'completed' THEN 1 END) as completed_appointments,
    COUNT(CASE WHEN ar.status = 'pending' THEN 1 END) as pending_requests
FROM patients p
CROSS JOIN appointment_requests ar;

-- Note: Remember to update passwords with actual hashed passwords when setting up users
-- The passwords shown here are dummy hashes and should be replaced with real hashed passwords