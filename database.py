import mysql.connector
from mysql.connector import Error

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'microsoft@900'
}

def create_database():
    """Create hospital database if it doesn't exist"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS hospital_management")
        print("Database 'hospital_management' created successfully!")
        
        cursor.close()
        connection.close()
    except Error as e:
        print(f"Error creating database: {e}")

def get_db_connection():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database='hospital_management'
        )
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

def create_tables():
    """Create all necessary tables"""
    connection = get_db_connection()
    if connection is None:
        return
    
    cursor = connection.cursor()
    
    # Create Departments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            dept_id INT AUTO_INCREMENT PRIMARY KEY,
            dept_name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create Doctors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            specialization VARCHAR(100),
            dept_id INT,
            phone VARCHAR(15),
            email VARCHAR(100) UNIQUE,
            qualification VARCHAR(200),
            experience_years INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE SET NULL
        )
    """)
    
    # Create Patients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            date_of_birth DATE,
            gender ENUM('Male', 'Female', 'Other'),
            phone VARCHAR(15),
            email VARCHAR(100),
            address TEXT,
            blood_group VARCHAR(5),
            emergency_contact VARCHAR(15),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create Appointments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,
            doctor_id INT NOT NULL,
            appointment_date DATE NOT NULL,
            appointment_time TIME NOT NULL,
            status ENUM('Scheduled', 'Completed', 'Cancelled') DEFAULT 'Scheduled',
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
        )
    """)
    
    # Create Medical Records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medical_records (
            record_id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,
            doctor_id INT NOT NULL,
            appointment_id INT,
            diagnosis TEXT,
            prescription TEXT,
            notes TEXT,
            record_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE,
            FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE SET NULL
        )
    """)
    
    # Create Chatbot Q&A table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chatbot_qa (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question VARCHAR(500) NOT NULL,
            answer TEXT NOT NULL,
            category VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create Doctor Schedules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor_schedules (
            schedule_id INT AUTO_INCREMENT PRIMARY KEY,
            doctor_name VARCHAR(100) NOT NULL,
            department VARCHAR(100) NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create Room Allotments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS room_allotments (
            allotment_id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id_ref VARCHAR(50) NOT NULL,
            patient_name VARCHAR(100) NOT NULL,
            age INT NOT NULL,
            gender ENUM('Male', 'Female', 'Other') NOT NULL,
            contact_number VARCHAR(15) NOT NULL,
            room_type VARCHAR(50) NOT NULL,
            room_number VARCHAR(20) NOT NULL,
            bed_number VARCHAR(20) NOT NULL,
            admission_date DATE NOT NULL,
            doctor_name VARCHAR(100) NOT NULL,
            department VARCHAR(100) NOT NULL,
            diagnosis TEXT,
            status ENUM('Occupied', 'Discharged') DEFAULT 'Occupied',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create Vaccination Records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vaccination_records (
            vaccination_id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id_ref VARCHAR(50) NOT NULL,
            patient_name VARCHAR(100) NOT NULL,
            age INT NOT NULL,
            vaccine_name VARCHAR(100) NOT NULL,
            dose_number VARCHAR(20) NOT NULL,
            vaccination_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    connection.commit()
    print("All tables created successfully!")
    
    # Insert predefined chatbot questions and answers
    cursor.execute("SELECT COUNT(*) as count FROM chatbot_qa")
    count = cursor.fetchone()[0]
    
    if count == 0:
        qa_data = [
            ('Hospital Hours', 'Our hospital is open 24/7 for emergency services. OPD timings are Monday to Saturday: 9:00 AM - 5:00 PM. Sunday: 9:00 AM - 1:00 PM.', 'General'),
            ('Book Appointment', 'You can book an appointment by clicking on the "Appointments" section in the navigation menu, or call us at +91-XXX-XXX-XXXX.', 'Appointments'),
            ('Emergency Contact', '🚨 For emergencies, please call our 24/7 helpline: +91-XXX-XXX-XXXX or visit our Emergency Department immediately.', 'Emergency'),
            ('Departments', 'We have the following departments: Cardiology, Neurology, Orthopedics, Pediatrics, General Medicine, Surgery, and more. Visit the Departments page for complete details.', 'Departments'),
            ('Visitor Policy', 'Visiting hours are 8:00 AM - 6:00 PM daily. Maximum 2 visitors per patient. Please carry a valid ID card.', 'General'),
            ('how to register', 'You can register as a new patient by visiting our reception desk with a valid ID proof and address proof, or use the Patients section in our system.', 'Registration'),
            ('doctor availability', 'Our doctors are available during OPD hours. For specific doctor availability, please check the Doctors section or call our reception.', 'Doctors'),
            ('payment methods', 'We accept Cash, Credit/Debit Cards, UPI, Net Banking, and Health Insurance. Please contact our billing department for insurance claims.', 'Billing'),
            ('medical records', 'You can access your medical records through our Medical Records section. Please bring your patient ID and valid identification.', 'Records'),
            ('ambulance service', 'Yes, we provide 24/7 ambulance services. Call our emergency number +91-XXX-XXX-XXXX for immediate assistance.', 'Emergency'),
            ('laboratory services', 'Our laboratory is open from 7:00 AM - 7:00 PM on weekdays and 8:00 AM - 2:00 PM on weekends. Most reports are available within 24 hours.', 'Laboratory'),
            ('pharmacy timings', 'Our in-house pharmacy is open 24/7 to serve you.', 'Pharmacy'),
            ('insurance', 'We accept most major health insurance providers. Please bring your insurance card and policy details during registration.', 'Insurance'),
            ('location', 'We are located at [Hospital Address]. You can find detailed directions on our website or contact us for assistance.', 'General'),
            ('covid guidelines', 'Please wear masks, maintain social distancing, and sanitize your hands. Temperature screening is mandatory at entry.', 'Safety'),
            ('parking facility', 'We have ample parking space available for patients and visitors. Parking charges apply for stays longer than 2 hours.', 'Facilities'),
            ('cafeteria timings', 'Our cafeteria is open from 7:00 AM - 9:00 PM. We serve breakfast, lunch, and dinner.', 'Facilities'),
            ('blood bank', 'Yes, we have a fully functional blood bank. For blood donation or requirements, please contact our blood bank department.', 'Services'),
            ('opd timings', 'OPD timings are Monday to Saturday: 9:00 AM - 5:00 PM. Sunday: 9:00 AM - 1:00 PM. Please book appointments in advance.', 'General'),
            ('vaccination', 'We provide all types of vaccinations for children and adults. Please check with our vaccination department for schedules.', 'Services')
        ]
        
        cursor.executemany(
            "INSERT INTO chatbot_qa (question, answer, category) VALUES (%s, %s, %s)",
            qa_data
        )
        connection.commit()
        print("Chatbot Q&A data inserted successfully!")
    
    cursor.close()
    connection.close()

def create_login_tables():
    """Create tables for login system"""
    connection = get_db_connection()
    if connection is None:
        return
    
    cursor = connection.cursor()
    
    # Create Admins table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert default admin (password: admin123)
    cursor.execute("SELECT COUNT(*) as count FROM admins")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Default admin credentials
        cursor.execute("""
            INSERT INTO admins (username, password) 
            VALUES ('admin', 'admin123')
        """)
        connection.commit()
        print("Default admin created: username='admin', password='admin123'")
    
    connection.commit()
    cursor.close()
    connection.close()
    print("Login tables created successfully!")

def initialize_database():
    """Initialize the complete database"""
    create_database()
    create_tables()
    create_login_tables()
    print("Database initialization completed!")

if __name__ == "__main__":
    initialize_database()