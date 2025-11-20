import mysql.connector
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   url_for, session)
from functools import wraps

from database import get_db_connection, initialize_database

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_in_production_12345'

# Initialize database on first run
try:
    initialize_database()
except:
    pass

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'danger')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'admin':
            flash('Admin access required!', 'danger')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# Restrict patients from add/update/delete operations
def restrict_patient_actions(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') == 'patient':
            flash('Patients can only view records, not modify them!', 'danger')
            return redirect(request.referrer or url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ============ LOGIN ROUTES ============
@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM admins WHERE username=%s AND password=%s", 
                      (username, password))
        admin = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if admin:
            session['user_id'] = admin['admin_id']
            session['username'] = admin['username']
            session['user_type'] = 'admin'
            flash('Welcome Admin! Login successful.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'danger')
            return redirect(url_for('admin_login'))
    
    return render_template('admin_login.html')

@app.route('/patient_login', methods=['GET', 'POST'])
def patient_login():
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        email = request.form['email']
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM patients WHERE patient_id=%s AND email=%s", 
                      (patient_id, email))
        patient = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if patient:
            session['user_id'] = patient['patient_id']
            session['patient_id'] = patient['patient_id']  # Store patient_id separately
            session['patient_name'] = f"{patient['first_name']} {patient['last_name']}"
            session['user_type'] = 'patient'
            flash(f'Welcome {patient["first_name"]}! Login successful.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid Patient ID or Email!', 'danger')
            return redirect(url_for('patient_login'))
    
    return render_template('patient_login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login_page'))

# Home Route
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# ============ DEPARTMENTS ROUTES ============
@app.route('/departments')
@login_required
def departments():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM departments ORDER BY dept_id ASC")
    departments = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('departments.html', departments=departments)

@app.route('/departments/add', methods=['POST'])
@restrict_patient_actions
def add_department():
    dept_name = request.form['dept_name']
    description = request.form['description']
    
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO departments (dept_name, description) VALUES (%s, %s)", 
                    (dept_name, description))
        connection.commit()
        flash('Department added successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('departments'))

@app.route('/departments/update/<int:id>', methods=['POST'])
@restrict_patient_actions
def update_department(id):
    dept_name = request.form['dept_name']
    description = request.form['description']
    
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE departments SET dept_name=%s, description=%s WHERE dept_id=%s",
                    (dept_name, description, id))
        connection.commit()
        flash('Department updated successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('departments'))

@app.route('/departments/delete/<int:id>')
@restrict_patient_actions
def delete_department(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM departments WHERE dept_id=%s", (id,))
        connection.commit()
        flash('Department deleted successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('departments'))

# ============ DOCTORS ROUTES ============
@app.route('/doctors')
@login_required
def doctors():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT d.*, dep.dept_name 
        FROM doctors d 
        LEFT JOIN departments dep ON d.dept_id = dep.dept_id 
        ORDER BY d.doctor_id ASC
    """)
    doctors = cursor.fetchall()
    
    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return render_template('doctors.html', doctors=doctors, departments=departments)

@app.route('/doctors/add', methods=['POST'])
@restrict_patient_actions
def add_doctor():
    data = request.form
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO doctors (first_name, last_name, specialization, dept_id, 
                            phone, email, qualification, experience_years)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (data['first_name'], data['last_name'], data['specialization'], 
            data['dept_id'], data['phone'], data['email'], 
            data['qualification'], data['experience_years']))
        connection.commit()
        flash('Doctor added successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('doctors'))

@app.route('/doctors/update/<int:id>', methods=['POST'])
@restrict_patient_actions
def update_doctor(id):
    data = request.form
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE doctors SET first_name=%s, last_name=%s, specialization=%s, 
                dept_id=%s, phone=%s, email=%s, qualification=%s, experience_years=%s
            WHERE doctor_id=%s
        """, (data['first_name'], data['last_name'], data['specialization'],
            data['dept_id'], data['phone'], data['email'],
            data['qualification'], data['experience_years'], id))
        connection.commit()
        flash('Doctor updated successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('doctors'))

@app.route('/doctors/delete/<int:id>')
@restrict_patient_actions
def delete_doctor(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM doctors WHERE doctor_id=%s", (id,))
        connection.commit()
        flash('Doctor deleted successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('doctors'))

# ============ PATIENTS ROUTES ============
@app.route('/patients')
@login_required
def patients():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Filter for patients - only show their own record
    if session.get('user_type') == 'patient':
        cursor.execute("SELECT * FROM patients WHERE patient_id=%s", (session.get('patient_id'),))
    else:
        cursor.execute("SELECT * FROM patients ORDER BY patient_id ASC")
    
    patients = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('patients.html', patients=patients)

@app.route('/patients/add', methods=['POST'])
@restrict_patient_actions
def add_patient():
    data = request.form
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO patients (first_name, last_name, date_of_birth, gender,
                                phone, email, address, blood_group, emergency_contact)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (data['first_name'], data['last_name'], data['date_of_birth'],
            data['gender'], data['phone'], data['email'], data['address'],
            data['blood_group'], data['emergency_contact']))
        connection.commit()
        flash('Patient added successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('patients'))

@app.route('/patients/update/<int:id>', methods=['POST'])
@restrict_patient_actions
def update_patient(id):
    data = request.form
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE patients SET first_name=%s, last_name=%s, date_of_birth=%s,
                gender=%s, phone=%s, email=%s, address=%s, blood_group=%s,
                emergency_contact=%s
            WHERE patient_id=%s
        """, (data['first_name'], data['last_name'], data['date_of_birth'],
            data['gender'], data['phone'], data['email'], data['address'],
            data['blood_group'], data['emergency_contact'], id))
        connection.commit()
        flash('Patient updated successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('patients'))

@app.route('/patients/delete/<int:id>')
@restrict_patient_actions
def delete_patient(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM patients WHERE patient_id=%s", (id,))
        connection.commit()
        flash('Patient deleted successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('patients'))

# ============ APPOINTMENTS ROUTES ============
@app.route('/appointments')
@login_required
def appointments():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Filter appointments for patients - only show their own appointments
    if session.get('user_type') == 'patient':
        cursor.execute("""
            SELECT a.*, 
                CONCAT(p.first_name, ' ', p.last_name) as patient_name,
                CONCAT(d.first_name, ' ', d.last_name) as doctor_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            WHERE a.patient_id = %s
            ORDER BY a.appointment_date DESC, a.appointment_time ASC
        """, (session.get('patient_id'),))
    else:
        cursor.execute("""
            SELECT a.*, 
                CONCAT(p.first_name, ' ', p.last_name) as patient_name,
                CONCAT(d.first_name, ' ', d.last_name) as doctor_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            ORDER BY a.appointment_date DESC, a.appointment_time ASC
        """)
    
    appointments = cursor.fetchall()
    
    cursor.execute("SELECT patient_id, CONCAT(first_name, ' ', last_name) as name FROM patients")
    patients = cursor.fetchall()
    
    cursor.execute("SELECT doctor_id, CONCAT(first_name, ' ', last_name) as name FROM doctors")
    doctors = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return render_template('appointments.html', appointments=appointments, 
                        patients=patients, doctors=doctors)

@app.route('/appointments/add', methods=['POST'])
@restrict_patient_actions
def add_appointment():
    data = request.form
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO appointments (patient_id, doctor_id, appointment_date,
                                    appointment_time, status, reason)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (data['patient_id'], data['doctor_id'], data['appointment_date'],
            data['appointment_time'], data['status'], data['reason']))
        connection.commit()
        flash('Appointment scheduled successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('appointments'))

@app.route('/appointments/update/<int:id>', methods=['POST'])
@restrict_patient_actions
def update_appointment(id):
    data = request.form
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE appointments SET patient_id=%s, doctor_id=%s, appointment_date=%s,
                appointment_time=%s, status=%s, reason=%s
            WHERE appointment_id=%s
        """, (data['patient_id'], data['doctor_id'], data['appointment_date'],
            data['appointment_time'], data['status'], data['reason'], id))
        connection.commit()
        flash('Appointment updated successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('appointments'))

@app.route('/appointments/delete/<int:id>')
@restrict_patient_actions
def delete_appointment(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM appointments WHERE appointment_id=%s", (id,))
        connection.commit()
        flash('Appointment deleted successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('appointments'))

# ============ MEDICAL RECORDS ROUTES ============
@app.route('/medical_records')
@login_required
def medical_records():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Filter medical records for patients - only show their own records
    if session.get('user_type') == 'patient':
        cursor.execute("""
            SELECT mr.*, 
                CONCAT(p.first_name, ' ', p.last_name) as patient_name,
                CONCAT(d.first_name, ' ', d.last_name) as doctor_name
            FROM medical_records mr
            JOIN patients p ON mr.patient_id = p.patient_id
            JOIN doctors d ON mr.doctor_id = d.doctor_id
            WHERE mr.patient_id = %s
            ORDER BY mr.record_date DESC
        """, (session.get('patient_id'),))
    else:
        cursor.execute("""
            SELECT mr.*, 
                CONCAT(p.first_name, ' ', p.last_name) as patient_name,
                CONCAT(d.first_name, ' ', d.last_name) as doctor_name
            FROM medical_records mr
            JOIN patients p ON mr.patient_id = p.patient_id
            JOIN doctors d ON mr.doctor_id = d.doctor_id
            ORDER BY mr.record_date DESC
        """)
    
    records = cursor.fetchall()
    
    cursor.execute("SELECT patient_id, CONCAT(first_name, ' ', last_name) as name FROM patients")
    patients = cursor.fetchall()
    
    cursor.execute("SELECT doctor_id, CONCAT(first_name, ' ', last_name) as name FROM doctors")
    doctors = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return render_template('medical_records.html', records=records, 
                        patients=patients, doctors=doctors)

@app.route('/medical_records/add', methods=['POST'])
@restrict_patient_actions
def add_medical_record():
    data = request.form
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO medical_records (patient_id, doctor_id, diagnosis,
                                    prescription, notes, record_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (data['patient_id'], data['doctor_id'], data['diagnosis'],
            data['prescription'], data['notes'], data['record_date']))
        connection.commit()
        flash('Medical record added successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('medical_records'))

@app.route('/medical_records/update/<int:id>', methods=['POST'])
@restrict_patient_actions
def update_medical_record(id):
    data = request.form
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE medical_records SET patient_id=%s, doctor_id=%s, diagnosis=%s,
                prescription=%s, notes=%s, record_date=%s
            WHERE record_id=%s
        """, (data['patient_id'], data['doctor_id'], data['diagnosis'],
            data['prescription'], data['notes'], data['record_date'], id))
        connection.commit()
        flash('Medical record updated successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('medical_records'))

@app.route('/medical_records/delete/<int:id>')
@restrict_patient_actions
def delete_medical_record(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM medical_records WHERE record_id=%s", (id,))
        connection.commit()
        flash('Medical record deleted successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('medical_records'))

# ============ CHATBOT ROUTES ============
@app.route('/chatbot')
def chatbot_page():
    """Render the chatbot HTML page"""
    return render_template('chatbot.html')

@app.route('/chatbot/response', methods=['POST'])
def chatbot_response():
    """Handle chatbot queries and return responses from database"""
    data = request.get_json()
    user_message = data.get('message', '').lower().strip()
    
    if not user_message:
        return jsonify({'response': 'Please ask a question!'})
    
    connection = get_db_connection()
    if connection is None:
        return jsonify({'response': 'Sorry, I am unable to connect to the database right now. Please try again later.'})
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Search for matching question in database
        cursor.execute("""
            SELECT answer FROM chatbot_qa 
            WHERE LOWER(question) LIKE %s 
            ORDER BY id ASC 
            LIMIT 1
        """, (f'%{user_message}%',))
        result = cursor.fetchone()
        
        if result:
            response_message = result['answer']
        else:
            # Default response if no match found
            response_message = (
                "I apologize, but I don't have information about that. "
                "Please contact our reception at +91-XXX-XXX-XXXX or visit our help desk for assistance. "
                "You can also try asking about: Hospital Hours, Appointments, Emergency Contact, "
                "Departments, Visitor Policy, or other hospital services."
            )
        
        return jsonify({'response': response_message})
    
    except mysql.connector.Error as e:
        return jsonify({'response': f'Sorry, I encountered an error: {str(e)}'})
    
    finally:
        cursor.close()
        connection.close()

# ============ DOCTOR SCHEDULES ROUTES ============
@app.route('/doctor_schedules')
@login_required
def doctor_schedules():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM doctor_schedules ORDER BY schedule_id ASC")
    schedules = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('doctor_schedules.html', schedules=schedules)

@app.route('/doctor_schedules/add', methods=['POST'])
@restrict_patient_actions
def add_doctor_schedule():
    data = request.form
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO doctor_schedules (doctor_name, department, start_time, end_time)
            VALUES (%s, %s, %s, %s)
        """, (data['doctor_name'], data['department'], data['start_time'], data['end_time']))
        connection.commit()
        flash('Doctor schedule added successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('doctor_schedules'))

@app.route('/doctor_schedules/update/<int:id>', methods=['POST'])
@restrict_patient_actions
def update_doctor_schedule(id):
    data = request.form
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE doctor_schedules SET doctor_name=%s, department=%s, 
                start_time=%s, end_time=%s
            WHERE schedule_id=%s
        """, (data['doctor_name'], data['department'], data['start_time'], 
              data['end_time'], id))
        connection.commit()
        flash('Doctor schedule updated successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('doctor_schedules'))

@app.route('/doctor_schedules/delete/<int:id>')
@restrict_patient_actions
def delete_doctor_schedule(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM doctor_schedules WHERE schedule_id=%s", (id,))
        connection.commit()
        flash('Doctor schedule deleted successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('doctor_schedules'))

# ============ ROOM ALLOTMENTS ROUTES ============
@app.route('/room_allotments')
@login_required
def room_allotments():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Filter room allotments for patients - only show their own allotment
    if session.get('user_type') == 'patient':
        cursor.execute("SELECT * FROM room_allotments WHERE patient_id_ref=%s ORDER BY allotment_id ASC", 
                      (str(session.get('patient_id')),))
    else:
        cursor.execute("SELECT * FROM room_allotments ORDER BY allotment_id ASC")
    
    allotments = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('room_allotments.html', allotments=allotments)

@app.route('/room_allotments/add', methods=['POST'])
@restrict_patient_actions
def add_room_allotment():
    data = request.form
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO room_allotments (patient_id_ref, patient_name, age, gender,
                contact_number, room_type, room_number, bed_number, admission_date,
                doctor_name, department, diagnosis, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (data['patient_id_ref'], data['patient_name'], data['age'], data['gender'],
              data['contact_number'], data['room_type'], data['room_number'], 
              data['bed_number'], data['admission_date'], data['doctor_name'],
              data['department'], data['diagnosis'], data.get('status', 'Occupied')))
        connection.commit()
        flash('Room allotment added successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('room_allotments'))

@app.route('/room_allotments/update/<int:id>', methods=['POST'])
@restrict_patient_actions
def update_room_allotment(id):
    data = request.form
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE room_allotments SET patient_id_ref=%s, patient_name=%s, age=%s,
                gender=%s, contact_number=%s, room_type=%s, room_number=%s, 
                bed_number=%s, admission_date=%s, doctor_name=%s, department=%s,
                diagnosis=%s, status=%s
            WHERE allotment_id=%s
        """, (data['patient_id_ref'], data['patient_name'], data['age'], data['gender'],
              data['contact_number'], data['room_type'], data['room_number'],
              data['bed_number'], data['admission_date'], data['doctor_name'],
              data['department'], data['diagnosis'], data['status'], id))
        connection.commit()
        flash('Room allotment updated successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('room_allotments'))

@app.route('/room_allotments/discharge/<int:id>')
@restrict_patient_actions
def discharge_room_allotment(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE room_allotments SET status='Discharged' WHERE allotment_id=%s", (id,))
        connection.commit()
        flash('Patient discharged successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('room_allotments'))

@app.route('/room_allotments/delete/<int:id>')
@restrict_patient_actions
def delete_room_allotment(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM room_allotments WHERE allotment_id=%s", (id,))
        connection.commit()
        flash('Room allotment deleted successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('room_allotments'))

# ============ VACCINATION RECORDS ROUTES ============
@app.route('/vaccination_records')
@login_required
def vaccination_records():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Filter vaccination records for patients - only show their own records
    if session.get('user_type') == 'patient':
        cursor.execute("SELECT * FROM vaccination_records WHERE patient_id_ref=%s ORDER BY vaccination_id ASC",
                      (str(session.get('patient_id')),))
    else:
        cursor.execute("SELECT * FROM vaccination_records ORDER BY vaccination_id ASC")
    
    records = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('vaccination_records.html', records=records)

@app.route('/vaccination_records/add', methods=['POST'])
@restrict_patient_actions
def add_vaccination_record():
    data = request.form
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO vaccination_records (patient_id_ref, patient_name, age,
                vaccine_name, dose_number, vaccination_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (data['patient_id_ref'], data['patient_name'], data['age'],
            data['vaccine_name'], data['dose_number'], data['vaccination_date']))
        connection.commit()
        flash('Vaccination record added successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('vaccination_records'))

@app.route('/vaccination_records/update/<int:id>', methods=['POST'])
@restrict_patient_actions
def update_vaccination_record(id):
    data = request.form
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE vaccination_records SET patient_id_ref=%s, patient_name=%s, age=%s,
                vaccine_name=%s, dose_number=%s, vaccination_date=%s
            WHERE vaccination_id=%s
        """, (data['patient_id_ref'], data['patient_name'], data['age'],
              data['vaccine_name'], data['dose_number'], data['vaccination_date'], id))
        connection.commit()
        flash('Vaccination record updated successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('vaccination_records'))

@app.route('/vaccination_records/delete/<int:id>')
@restrict_patient_actions
def delete_vaccination_record(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM vaccination_records WHERE vaccination_id=%s", (id,))
        connection.commit()
        flash('Vaccination record deleted successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('vaccination_records'))

if __name__ == '__main__':
    app.run(debug=True)