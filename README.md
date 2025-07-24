# Hospital Management System - DBMS Project

## Overview
This is a **Flask-based Hospital Management System** developed as part of a university DBMS course project.  
It provides a secure and efficient way to manage hospital operations including doctor management, patient appointments, prescriptions, and medical history tracking.  

The system leverages:
- **Flask** for backend web framework
- **MySQL** for database management
- **Flask-Login** for authentication & user roles
- **Flask-Mail** for email notifications
- **SQLAlchemy ORM** for database interactions

---

## Features
- **Role-based Access**  
  - **Manager**: Add doctors, manage patients, approve/reject appointment requests, send reminders  
  - **Doctor**: View daily schedules, complete appointments, add prescriptions, manage patient history  
  - **Patient**: Book appointment requests, view history, check prescriptions  

- **Appointment Scheduling & Conflict Detection**  
  - Checks for time-slot conflicts before booking appointments.  
  - Supports **manager-driven bookings** and **patient appointment requests**.

- **Email Notifications**  
  - Confirmation emails for approved appointments.  
  - Rejection notifications.  
  - Daily appointment reminders (scheduled with `apscheduler`).

- **Medical Records**  
  - Stores and retrieves patient medical history and prescriptions securely.

---

## Tech Stack
- **Backend**: Python (Flask)  
- **Database**: MySQL  
- **ORM**: SQLAlchemy  
- **Authentication**: Flask-Login  
- **Email Service**: Flask-Mail (SMTP Gmail)  
- **Scheduling**: APScheduler  

---

