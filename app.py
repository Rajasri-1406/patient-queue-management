import os
import pyodbc
from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from datetime import datetime, timedelta
 
 
app = Flask(__name__)

# 🔹 Set a Secret Key for Flask Sessions
app.secret_key = 'your_secure_secret_key'  

# 🔹 Database Connection String
ODBC_CONNECTION_STRING = "DSN=user_dns_name;Uid=database_name;Pwd=password;"


from flask_mail import Mail, Message
from dotenv import load_dotenv
import os

load_dotenv()

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('GMAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('GMAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('GMAIL_USERNAME')

mail = Mail(app)


def get_db_connection():
    """Establish database connection."""
    try:
        connection = pyodbc.connect(ODBC_CONNECTION_STRING)
        return connection
    except pyodbc.DatabaseError as e:
        print(f"Database Connection Error: {e}")
        return None

def generate_time_slots(start_time_str, end_time_str, interval_minutes):
    start = datetime.strptime(start_time_str, "%H:%M")
    end = datetime.strptime(end_time_str, "%H:%M")
    slots = []
    while start < end:
        slots.append(start.strftime("%I:%M %p"))
        start += timedelta(minutes=interval_minutes)
    return slots
   

# =======================
# 🔹 Home Route (Loads home.html)
# =======================
@app.route('/')
def home():
    return render_template(
        'home.html',
        username=session.get('username'),
        role=session.get('role')
    )


@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        user_id = request.form['user_id']
        name = request.form['name']
        role = request.form['role']
        password = request.form['password']

        # ✅ Specialization is required only for doctors
        specialization = request.form.get('specialization') if role == "Doctor" else None

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT USER_ID FROM USERS1 WHERE USER_ID = ?", (user_id,))
        if cursor.fetchone():
            flash("User ID already exists! Choose a different ID.", "error")
            return redirect(url_for('create_user'))

        cursor.execute("""
            INSERT INTO USERS1 (USER_ID, NAME, ROLE, PASSWORD, SPECIALIZATION) 
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, role, password, specialization))

        conn.commit()
        conn.close()

        flash("User registered successfully! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('create_user.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        name = request.form['name']
        role = request.form['role']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        # ✅ Check if user exists
        cursor.execute("SELECT COUNT(*) FROM USERS1 WHERE USER_ID = ?", (user_id,))
        if cursor.fetchone()[0] == 0:
            flash("User does not exist! Please create an account to login.", "error")
            return render_template('login.html')

        # ✅ Fetch user info
        cursor.execute("""
            SELECT U.USER_ID, U.NAME, U.ROLE, P.AGE, P.GENDER, P.STATUS, P.CONTACT
            FROM USERS1 U 
            LEFT JOIN PATIENT_TRIAGE P ON U.USER_ID = P.PATIENT_ID
            WHERE U.USER_ID = ? AND U.NAME = ? AND U.ROLE = ? AND U.PASSWORD = ?
        """, (user_id, name, role, password))

        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[2]

            if session['role'] == 'Patient':
                try:
                    session['age'] = int(float(user[3])) if user[3] else "N/A"
                except ValueError:
                    session['age'] = "N/A"

                session['gender'] = user[4] if user[4] else "N/A"
                session['status'] = user[5] if user[5] else "N/A"
                session['contact'] = user[6] if user[6] else ""

                conn.close()
                flash(f"Welcome, {user[1]}!", "success")
                return redirect(url_for('home'))

            conn.close()
            flash(f"Welcome, {user[1]}!", "success")

            if session['role'] == 'Admin':
                return redirect(url_for('home'))
            if session['role'] == 'Doctor':
                return redirect(url_for('home'))

        conn.close()
        flash("Invalid login credentials. Try again.", "error")

    return render_template('login.html')



@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))



@app.route('/view_details', methods=['GET', 'POST'])
def view_details():
    if 'user_id' not in session or session['role'] != 'Patient':  # Check if user is logged in as a patient
        flash("Please log in as a patient first.", "error")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch patient info from the database
    cursor.execute("""
        SELECT PATIENT_ID, NAME, CONTACT, AGE, GENDER
        FROM PATIENT_TRIAGE
        WHERE PATIENT_ID = ?
    """, (session['user_id'],))

    row = cursor.fetchone()
    conn.close()

    if not row:  # If no patient record is found
        flash("No patient record found.", "error")
        return redirect(url_for('home'))

    # Prepare patient data
    patient = {
        'patient_id': row[0],
        'name': row[1],
        'contact': row[2],
        'age': row[3],
        'gender': row[4]
    }

    # Store patient details in session for use in triage form
    session['username'] = patient['name'] if patient['name'] else ""
    session['contact'] = patient['contact'] if patient['contact'] else ""
    try:
        session['age'] = int(float(patient['age'])) if patient['age'] else "N/A"
    except (ValueError, TypeError):
        session['age'] = "N/A"
    session['gender'] = patient['gender'] if patient['gender'] else "N/A"

    # Debug: show if contact was fetched
    print("Session contact:", session['contact'])

    # Render the template with patient details
    return render_template('view_details.html', patient=patient)


@app.route('/view_history')
def view_history():
    if 'username' not in session or session['role'] != 'Patient':
        flash("Please log in as a patient first.", "error")
        return redirect(url_for('login'))

    patient_name = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ Fetch history based on patient name
    cursor.execute("""
        SELECT DOCTOR_NAME, SPECIALIZATION, CRITICALITY, 
               TO_CHAR(APPOINTMENT_DATE, 'YYYY-MM-DD'), 
               APPOINTMENT_TIME, PRESCRIBED_MEDICINES, 
               PRESCRIPTION_DETAILS, ADDITIONAL_NOTES
        FROM PPD
        WHERE PATIENT_NAME = ?
        ORDER BY APPOINTMENT_DATE DESC, APPOINTMENT_TIME DESC
    """, (patient_name,))

    results = cursor.fetchall()
    conn.close()

    history = []
    for row in results:
        history.append({
            "doctor_name": row[0],
            "specialization": row[1],
            "criticality": row[2],
            "appointment_date": row[3],
            "appointment_time": row[4],
            "medicines": row[5],
            "prescription": row[6],
            "notes": row[7]
        })

    return render_template('view_history.html', history=history)


@app.route('/triage', methods=['GET', 'POST'])
def triage():
    if request.method == 'GET':
        conn = get_db_connection()
        cursor = conn.cursor()
        if 'user_id' in session and session.get('role') == 'Patient':
            patient_id = session['user_id']
        else:
            cursor.execute("SELECT COUNT(DISTINCT PATIENT_ID) FROM PATIENT_TRIAGE")
            count = cursor.fetchone()[0]
            patient_id = f"P{int(count) + 1:03d}"
        conn.close()
        return render_template('triage.html', patient_id=patient_id)

    # POST logic
    conn = get_db_connection()
    cursor = conn.cursor()

    # Step 1: Get patient details
    if 'user_id' in session and session.get('role') == 'Patient':
        patient_id = session['user_id']
        name = session.get('username', '')
        gender = session.get('gender', '')
        try:
            age = int(float(session.get('age', 0)))
        except:
            age = 0
        contact = session.get('contact', '')
        if not name or not contact:
            cursor.execute("""
    SELECT NAME, AGE, GENDER, CONTACT
    FROM (
        SELECT NAME, AGE, GENDER, CONTACT
        FROM PATIENT_TRIAGE
        WHERE PATIENT_ID = ?
    )
    WHERE ROWNUM = 1
""", (patient_id,))

            row = cursor.fetchone()
            if row:
                name, age, gender, contact = row[0], int(float(row[1])), row[2], row[3]
    else:
        cursor.execute("SELECT COUNT(DISTINCT PATIENT_ID) FROM PATIENT_TRIAGE")
        count = cursor.fetchone()[0]
        patient_id = f"P{int(count) + 1:03d}"
        name = request.form['name']
        age = int(request.form.get('age', 0))
        gender = request.form.get('gender', '')
        contact = request.form.get('contact', '')

    # Step 2: Extract form data
    symptoms = request.form['symptoms'].lower()
    history = request.form.get('history', '')
    specialization = request.form['specialization']
    doctor = request.form['doctor']
    appointment_date = request.form['appointment_date']
    bp = request.form.get('bp', 'N/A')
    heart_rate = int(request.form.get('heart_rate', 0))
    respiratory_rate = int(request.form.get('respiratory_rate', 0))
    oxygen_saturation = int(request.form.get('oxygen_saturation', 0))
    booking_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # ✅ Step 2.5: Enforce max 12 patients per day per doctor
    cursor.execute("""
        SELECT COUNT(*) FROM PATIENT_TRIAGE
        WHERE ASSIGNED_DOCTOR = ? AND APPOINTMENT_DATE = TO_DATE(?, 'YYYY-MM-DD')
    """, (doctor, appointment_date))
    count = cursor.fetchone()[0]

    if count >= 12:
        cursor.execute("""
    SELECT TO_CHAR(APPOINTMENT_DATE, 'YYYY-MM-DD')
    FROM (
        SELECT APPOINTMENT_DATE, COUNT(*) AS num
        FROM PATIENT_TRIAGE
        WHERE ASSIGNED_DOCTOR = ?
        GROUP BY APPOINTMENT_DATE
        HAVING COUNT(*) < 12
        ORDER BY APPOINTMENT_DATE
    )
    WHERE ROWNUM = 1
""", (doctor,))

        result = cursor.fetchone()
        if result:
            appointment_date = result[0]
        else:
            appointment_date = (datetime.strptime(appointment_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

    # Step 3: Determine Triage Level
    triage_mapping = {
        "Cardiology": {"Critical": ["heart attack", "severe chest pain", "cardiac arrest", "chest pain"],
                       "High": ["irregular heartbeat", "mild chest pain", "shortness of breath"],
                       "Moderate": ["palpitations", "mild breathlessness"],
                       "Low": ["occasional chest discomfort", "mild fatigue"]},
        "Neurology": {"Critical": ["stroke", "seizure", "loss of consciousness"],
                      "High": ["migraine", "numbness", "loss of coordination"],
                      "Moderate": ["dizziness", "tingling sensation"],
                      "Low": ["mild headache", "lightheadedness"]},
        "Orthopedics": {"Critical": ["compound fracture", "dislocated joint with bleeding"],
                        "High": ["bone fracture", "severe swelling", "dislocated joint"],
                        "Moderate": ["sprain", "moderate joint pain"],
                        "Low": ["muscle strain", "minor bruises"]},
        "Pediatrics": {"Critical": ["newborn fever", "severe dehydration"],
                       "High": ["high fever", "persistent cough", "difficulty breathing"],
                       "Moderate": ["sore throat", "moderate fever"],
                       "Low": ["runny nose", "mild cough"]},
        "General Medicine": {"Critical": ["sepsis", "unconsciousness"],
                             "High": ["severe fatigue", "high fever", "persistent vomiting"],
                             "Moderate": ["mild symptoms", "headache", "cold"],
                             "Low": ["seasonal allergies", "body aches"]}
    }

    triage_level = "Low"
    for level, keywords in triage_mapping.get(specialization, {}).items():
        if any(keyword in symptoms for keyword in keywords):
            triage_level = level
            break

    # Step 4: Insert patient (initially with NULL timing)
    cursor.execute("""
        INSERT INTO PATIENT_TRIAGE (
            PATIENT_ID, NAME, AGE, GENDER, CONTACT, SYMPTOMS, MEDICAL_HISTORY,
            TRIAGE_LEVEL, SPECIALIZATION, ESTIMATED_WAITING_TIME,
            APPOINTMENT_DATE, BP, HEART_RATE, RESPIRATORY_RATE, OXYGEN_SATURATION,
            ASSIGNED_DOCTOR, APPOINTMENT_TIME, BOOKING_DATETIME
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, TO_DATE(?, 'YYYY-MM-DD'), ?, ?, ?, ?, ?, NULL, TO_TIMESTAMP(?, 'YYYY-MM-DD HH24:MI:SS'))
    """, (
        patient_id, name, age, gender, contact, symptoms, history,
        triage_level, specialization, appointment_date,
        bp, heart_rate, respiratory_rate, oxygen_saturation,
        doctor, booking_time
    ))
    conn.commit()

    # Step 5: Re-fetch all patients for that doctor and date
    cursor.execute("""
        SELECT PATIENT_ID, TRIAGE_LEVEL, TO_CHAR(BOOKING_DATETIME, 'YYYY-MM-DD HH24:MI:SS')
        FROM PATIENT_TRIAGE
        WHERE ASSIGNED_DOCTOR = ? AND APPOINTMENT_DATE = TO_DATE(?, 'YYYY-MM-DD')
        ORDER BY 
            CASE TRIAGE_LEVEL
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Moderate' THEN 3
                WHEN 'Low' THEN 4
            END ASC,
            BOOKING_DATETIME ASC
    """, (doctor, appointment_date))
    existing = cursor.fetchall()

    # Step 6: Reassign times
    schedule = []
    current_time = datetime.strptime("09:00", "%H:%M")
    first_time = current_time

    # Assign first
    first_pid, first_level, _ = existing[0]
    schedule.append((first_pid, current_time.strftime("%H:%M")))
    increment = 15 if first_level in ("High", "Critical") else 10
    current_time += timedelta(minutes=increment)

    for pid, level, _ in existing[1:]:
        schedule.append((pid, current_time.strftime("%H:%M")))
        increment = 15 if level in ("High", "Critical") else 10
        current_time += timedelta(minutes=increment)

    # Step 7: Update DB
    for pid, time_slot in schedule:
        wait_min = int((datetime.strptime(time_slot, "%H:%M") - first_time).total_seconds() // 60)
        wait_text = f"{wait_min} mins" if wait_min > 0 else "Immediate"

        cursor.execute("""
            UPDATE PATIENT_TRIAGE
            SET APPOINTMENT_DATE = TO_DATE(?, 'YYYY-MM-DD'),
                APPOINTMENT_TIME = ?,
                ESTIMATED_WAITING_TIME = ?
            WHERE PATIENT_ID = ?
        """, (appointment_date, time_slot, wait_text, pid))

        if pid == patient_id:
            appointment_time = time_slot
            waiting_time = wait_text

    conn.commit()
    conn.close()

    return redirect(url_for('triage_results',
                            patient_id=patient_id, name=name, age=age, gender=gender,
                            contact=contact, symptoms=symptoms, history=history,
                            triage=triage_level,
                            specialization=specialization,
                            wait=waiting_time,
                            doctor=doctor, date=appointment_date, time=appointment_time))

@app.route('/queue')
def queue():
    if 'user_id' not in session or session['role'] != 'Patient':
        flash("Please log in as a patient first.", "error")
        return redirect(url_for('login'))

    patient_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch logged-in patient's details
    cursor.execute("""
        SELECT P.PATIENT_ID, P.NAME, P.AGE, P.SPECIALIZATION, 
               U.NAME AS DOCTOR_NAME, P.ASSIGNED_DOCTOR,
               TO_CHAR(P.APPOINTMENT_DATE, 'YYYY-MM-DD') AS APPOINTMENT_DATE
        FROM PATIENT_TRIAGE P
        LEFT JOIN USERS1 U ON P.ASSIGNED_DOCTOR = U.USER_ID  
        WHERE P.PATIENT_ID = ?
    """, (patient_id,))
    patient_details = cursor.fetchone()

    if not patient_details:
        flash("No appointment found for the logged-in patient.", "error")
        conn.close()
        return redirect(url_for('home'))

    # Fetch queue data including 12-hour formatted appointment time
    cursor.execute("""
        SELECT 
            P.PATIENT_ID, P.NAME AS PATIENT_NAME, U.NAME AS DOCTOR_NAME, 
            P.SPECIALIZATION, 
            TO_CHAR(P.APPOINTMENT_DATE, 'YYYY-MM-DD') AS APPT_DATE, 
            P.APPOINTMENT_TIME AS APPT_TIME, 
            P.TRIAGE_LEVEL, P.AGE, 
            TO_CHAR(P.BOOKING_DATETIME, 'YYYY-MM-DD HH24:MI:SS') AS BOOKING_DATETIME
        FROM PATIENT_TRIAGE P
        LEFT JOIN USERS1 U ON P.ASSIGNED_DOCTOR = U.USER_ID  
        WHERE P.STATUS IS NOT NULL AND P.STATUS != 'Diagnosed'
        ORDER BY 
            CASE P.TRIAGE_LEVEL  
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Moderate' THEN 3
                WHEN 'Low' THEN 4
            END ASC,
            P.BOOKING_DATETIME ASC, 
            P.AGE DESC
    """)
    queue_data = cursor.fetchall()
    conn.close()

    return render_template('queue.html', queue_data=queue_data, patient_details=patient_details)


@app.route('/view_appointment', methods=['GET', 'POST'])
def view_appointment():
    if 'user_id' not in session or session['role'] != 'Patient':  # Check if user is logged in as a patient
        flash("Please log in as a patient first.", "error")
        return redirect(url_for('login'))
    
    patient_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query to fetch pending appointments for the logged-in patient
    query = """
        SELECT 
            PT.PATIENT_ID,
            PT.NAME AS PATIENT_NAME,
            PT.CONTACT,
            PT.AGE,
            PT.GENDER,
            PT.SPECIALIZATION,
            U.NAME AS DOCTOR_NAME,
            TO_CHAR(PT.APPOINTMENT_DATE, 'YYYY-MM-DD') AS APPOINTMENT_DATE,
            PT.APPOINTMENT_TIME,
            PT.STATUS
        FROM 
            PATIENT_TRIAGE PT
        LEFT JOIN 
            USERS1 U 
        ON 
            PT.ASSIGNED_DOCTOR = U.USER_ID
        WHERE 
            PT.PATIENT_ID = ? AND PT.STATUS = 'Pending'
        ORDER BY 
            PT.APPOINTMENT_DATE DESC
    """
    
    cursor.execute(query, (patient_id,))
    appointments = cursor.fetchall()
    cursor.close()
    conn.close()

    # If no appointments are found, display a message
    if not appointments:
        flash("You have no pending appointments.", "info")

    return render_template("view_appointment.html", appointments=appointments)


@app.route('/admin_dashboard')
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch appointments
    cursor.execute("""
    SELECT PATIENT_ID, NAME, SPECIALIZATION, 
           TO_CHAR(APPOINTMENT_DATE, 'YYYY-MM-DD') AS APPOINTMENT_DATE, 
           APPOINTMENT_TIME, ASSIGNED_DOCTOR, STATUS, 
           TO_CHAR(BOOKING_DATETIME, 'YYYY-MM-DD HH24:MI:SS') AS BOOKING_DATETIME
    FROM PATIENT_TRIAGE
    WHERE STATUS='Pending'
    ORDER BY APPOINTMENT_DATE DESC, APPOINTMENT_TIME ASC
    """)
    appointments = cursor.fetchall()

    # Fetch walk-in patients and convert rows to plain lists
    cursor.execute("SELECT * FROM walkins ORDER BY token_no ASC")
    walkin_rows = cursor.fetchall()
    walkins = [list(row) for row in walkin_rows]  # ✅ Convert to list of lists

    conn.close()

    return render_template('admin_dashboard.html', appointments=appointments, walkins=walkins)

@app.route("/doctor_list", methods=["GET"])
def doctor_list():
    """Fetch all doctors and order them by the number of patients scheduled."""
    if 'username' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Query to fetch all doctors and their available days from DOCTOR_SCHEDULE
        cursor.execute("""
            SELECT DOCTOR_ID, DOCTOR_NAME, AVAILABLE_DAYS 
            FROM DOCTOR_SCHEDULE;
        """)

        # Debugging: Print column names
        columns = [column[0] for column in cursor.description]
        print(f"Columns in DOCTOR_SCHEDULE: {columns}")  # Debugging output

        doctors = cursor.fetchall()

        doctor_patient_counts = []

        for doctor in doctors:
            doctor_id, doctor_name, available_days = doctor

            # Debugging output for fetched doctor data
            print(f"Doctor: {doctor_id}, {doctor_name}, {available_days}")

            # Fetch the number of patients for this doctor
            cursor.execute("""
                SELECT COUNT(*) 
                FROM PATIENT_TRIAGE
                WHERE ASSIGNED_DOCTOR = ?;
            """, (doctor_id))

            # Debugging: Print patient count for this doctor
            patient_count = int(cursor.fetchone()[0])
            print(f"Patient count for Doctor {doctor_name}: {patient_count}")  # Debugging output

            # Append doctor details along with patient count
            doctor_patient_counts.append({
                "id": doctor_id,
                "name": doctor_name,
                "days": available_days,
                "patients": patient_count
            })

        # Sort doctors by patient count in descending order
        doctor_patient_counts.sort(key=lambda x: x['patients'], reverse=True)

        conn.close()

        # Render the list of doctors ordered by patient count
        return render_template("doctor_list.html", doctor_patient_counts=doctor_patient_counts)

    except Exception as e:
        # Catch any exceptions and print them for debugging
        print(f"Error fetching doctor list: {str(e)}")
        conn.close()
        return jsonify({"error": str(e)})

@app.route('/update_appointment', methods=['POST'])
def update_appointment():
    """Handles appointment cancellation and rescheduling based on patient ID and specialization."""
    
    # Ensure patient is logged in
    if 'user_id' not in session or session.get('role') != 'Patient':
        flash("Please log in as a patient first.", "error")
        return redirect(url_for('login'))

    patient_id = session['user_id']
    action = request.form.get("action")
    specialization = request.form.get("specialization")
    appointment_date = request.form.get("appointment_date")

    print(f"[DEBUG] Action: {action}, Patient ID: {patient_id}, Specialization: {specialization}, Date: {appointment_date}")

    # Validate required inputs
    if not specialization or not appointment_date:
        flash("Missing specialization or date.", "error")
        return redirect(url_for('view_appointment'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if action == "cancel":
            cursor.execute("""
                UPDATE PATIENT_TRIAGE
                SET STATUS = 'Diagnosed'
                WHERE TRIM(LOWER(PATIENT_ID)) = :1 
                  AND TRIM(LOWER(SPECIALIZATION)) = :2
                  AND TO_CHAR(APPOINTMENT_DATE, 'YYYY-MM-DD') = :3
            """, (patient_id.lower().strip(), specialization.lower().strip(), appointment_date))
            conn.commit()
            flash("Your appointment has been canceled and marked as diagnosed.", "success")

        elif action == "reschedule":
            # Set new appointment date & time (7 days later)
            new_date = (datetime.strptime(appointment_date, '%Y-%m-%d') + timedelta(days=7)).strftime('%Y-%m-%d')
            new_time = "9:00 AM"  # You can allow dynamic selection later

            cursor.execute("""
                UPDATE PATIENT_TRIAGE
                SET APPOINTMENT_DATE = TO_DATE(:1, 'YYYY-MM-DD'), APPOINTMENT_TIME = :2
                WHERE TRIM(LOWER(PATIENT_ID)) = :3
                  AND TRIM(LOWER(SPECIALIZATION)) = :4
                  AND TO_CHAR(APPOINTMENT_DATE, 'YYYY-MM-DD') = :5
            """, (new_date, new_time, patient_id.lower().strip(), specialization.lower().strip(), appointment_date))
            conn.commit()
            flash("Your appointment has been rescheduled successfully.", "success")

        else:
            flash("Invalid action received.", "error")

    except Exception as e:
        print(f"[ERROR] Failed to update appointment: {e}")
        flash("Database error while updating appointment.", "error")

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return redirect(url_for('view_appointment'))



@app.route('/doctor_home')
def doctor_home():
    # Ensure the user is logged in and has the 'Doctor' role
    if 'username' not in session or session.get('role') != 'Doctor':
        return redirect(url_for('login'))

    # Retrieve doctor details from session
    doctor_id = session.get('user_id')
    doctor_name = session.get('username')

    # Connect to the database (replace with your connection details)
    conn = get_db_connection()  # Assuming you have a function to get DB connection
    cursor = conn.cursor()

    try:
        # Query to get the specialization and available days for the doctor
        query = """
            SELECT specialization, available_days 
            FROM doctor_schedule 
            WHERE doctor_id = ?
        """
        
        # Print query and parameters for debugging
        print(f"Executing query: {query} with doctor_id: {doctor_id}")

        # Execute the query with parameter binding for pyodbc (using ? placeholder)
        cursor.execute(query, (doctor_id,))

        # Fetch the result
        result = cursor.fetchone()

        # Debugging output
        print(f"Query Result: {result}")  # Add this line to check the fetched data

        # If no result is found, set default values for specialization and available days
        if result:
            specialization, available_days = result
        else:
            specialization, available_days = "Not Available", "Not Available"

    except Exception as e:
        # Log or handle any exceptions that occur during the DB query
        print(f"Error fetching doctor schedule: {str(e)}")
        specialization, available_days = "Not Available", "Not Available"

    finally:
        # Close the database connection
        conn.close()

    # Create doctor dictionary to pass to the template
    doctor = {
        'id': doctor_id,
        'name': doctor_name,
        'specialization': specialization,
        'available_days': available_days
    }

    # Render the doctor_home.html template with the doctor data
    return render_template('doctor_home.html', doctor=doctor)



@app.route('/doctor_dashboard')
def doctor_dashboard():
    if 'role' not in session or session['role'] != 'Doctor':
        flash("Unauthorized Access!", "error")
        return redirect(url_for('login'))

    doctor_id = session['user_id']
    doctor_name = session['username']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch specialization
    cursor.execute("SELECT SPECIALIZATION FROM USERS1 WHERE USER_ID = ?", (doctor_id,))
    specialization = cursor.fetchone()
    specialization = specialization[0] if specialization else "General Medicine"

    # ✅ Updated Query
    cursor.execute("""
        SELECT PATIENT_ID, NAME, TO_CHAR(APPOINTMENT_DATE, 'YYYY-MM-DD'),
               APPOINTMENT_TIME, STATUS, TRIAGE_LEVEL
        FROM PATIENT_TRIAGE
        WHERE ASSIGNED_DOCTOR = ?
        ORDER BY 
            CASE TRIAGE_LEVEL
                WHEN 'Critical' THEN 4
                WHEN 'High' THEN 3
                WHEN 'Moderate' THEN 2
                WHEN 'Low' THEN 1
                ELSE 0
            END DESC,
            APPOINTMENT_DATE ASC,
            APPOINTMENT_TIME ASC
    """, (doctor_id,))

    patients = cursor.fetchall()
    conn.close()

    return render_template('doctor_dashboard.html',
                           doctor_id=doctor_id,
                           doctor_name=doctor_name,
                           specialization=specialization,
                           patients=patients)

@app.route('/diagnose/<string:patient_id>/<string:specialization>', methods=['GET'])
def diagnose(patient_id, specialization):
    if 'user_id' not in session or session['role'] != 'Doctor':
        flash("Unauthorized access!", "error")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ✅ Fetch patient triage data specific to the doctor and specialization
    cursor.execute("""
        SELECT PATIENT_ID, NAME, SYMPTOMS, SPECIALIZATION, TRIAGE_LEVEL, 
               TO_CHAR(APPOINTMENT_DATE, 'YYYY-MM-DD'), APPOINTMENT_TIME
        FROM PATIENT_TRIAGE
        WHERE PATIENT_ID = ? AND SPECIALIZATION = ?
    """, (patient_id, specialization))
    
 
    
    row = cursor.fetchone()

    if not row:
        flash("No matching appointment found for this patient and specialization!", "error")
        conn.close()
        return redirect(url_for('doctor_dashboard'))

    patient = {
        "patient_id": row[0],
        "name": row[1],
        "symptoms": row[2],
        "specialization": row[3],
        "triage_level": row[4],
        "appointment_date": row[5],
        "appointment_time": row[6]
    }

    conn.close()

    return render_template('diagnose_form.html',
                           patient=patient,
                           doctor_id=session['user_id'],
                           doctor_name=session['username'])

@app.route('/submit_diagnosis', methods=['POST'])
def submit_diagnosis():
    data = request.form

    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ Insert diagnosis data
    cursor.execute("""
        INSERT INTO PPD (PATIENT_ID, PATIENT_NAME, DOCTOR_ID, DOCTOR_NAME, SPECIALIZATION, 
                         CRITICALITY, APPOINTMENT_DATE, APPOINTMENT_TIME, 
                         PRESCRIBED_MEDICINES, PRESCRIPTION_DETAILS, ADDITIONAL_NOTES)
        VALUES (?, ?, ?, ?, ?, ?, TO_DATE(?, 'YYYY-MM-DD'), ?, ?, ?, ?)
    """, (
        data['patient_id'],
        data['patient_name'],
        data['doctor_id'],
        data['doctor_name'],
        data['specialization'],
        data['criticality'],
        data['appointment_date'],
        data['appointment_time'],
        data['medicines'],
        data['prescription_details'],
        data['additional_notes']
    ))

    # ✅ Update only that specific triage record
    cursor.execute("""
        UPDATE PATIENT_TRIAGE 
        SET STATUS = 'Diagnosed' 
        WHERE PATIENT_ID = ? AND SPECIALIZATION = ?
    """, (data['patient_id'], data['specialization']))

    conn.commit()
    conn.close()

    flash("Diagnosis submitted successfully!", "success")
    return redirect(url_for('doctor_dashboard'))


@app.route("/get_doctors", methods=["POST"])
def get_doctors():
    """Fetch doctors based on specialization."""
    data = request.get_json()
    specialization = data.get("specialization", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DOCTOR_ID, DOCTOR_NAME, AVAILABLE_DAYS 
        FROM DOCTOR_SCHEDULE 
        WHERE SPECIALIZATION = ?;
    """, (specialization,))
    
    doctors = cursor.fetchall()
    conn.close()

    if not doctors:
        return jsonify([])  # Return empty list if no doctors found

    return jsonify([{"id": doc[0], "name": doc[1], "days": doc[2]} for doc in doctors])


@app.route('/toggle_doctor_availability', methods=['GET'])
def toggle_doctor_availability():
    if 'user_id' not in session or session['role'] != 'Doctor':
        return jsonify({'message': 'Unauthorized'}), 403

    doctor_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ Get current status
    cursor.execute("SELECT STATUS FROM DOCTORS WHERE DOCTOR_ID = ?", (doctor_id,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return jsonify({'message': 'Doctor not found'}), 404

    # ✅ Toggle status
    new_status = "Available" if result[0] == "Unavailable" else "Unavailable"
    cursor.execute("UPDATE DOCTORS SET STATUS = ? WHERE DOCTOR_ID = ?", (new_status, doctor_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Status updated successfully', 'new_status': new_status})

@app.route("/send_email", methods=["POST"])
def send_email():
    # Retrieve form data
    patient_id = request.form.get('patient_id')
    recipient_email = request.form.get('email')

    # Get all patient details from the form
    patient_name = request.form.get('name')
    patient_age = request.form.get('age')
    patient_gender = request.form.get('gender')
    patient_contact = request.form.get('contact')
    patient_symptoms = request.form.get('symptoms')
    patient_specialization = request.form.get('specialization')
    patient_doctor = request.form.get('doctor')
    patient_date = request.form.get('date')
    patient_time = request.form.get('time')
    patient_triage = request.form.get('triage')
    patient_wait = request.form.get('wait')

    if not recipient_email:
        return "Error: Email is required", 400

    try:
        msg = Message(f"Appointment Details for {patient_name}",
                      recipients=[recipient_email])

        msg.body = f"""
        Patient ID: {patient_id}
        Name: {patient_name}
        Age: {patient_age}
        Gender: {patient_gender}
        Contact: {patient_contact}
        Symptoms: {patient_symptoms}
        Specialization: {patient_specialization}
        Assigned Doctor: {patient_doctor}
        Appointment Date: {patient_date}
        Appointment Time: {patient_time}
        Triage Level: {patient_triage}
        Estimated Waiting Time: {patient_wait}
        """
        mail.send(msg)
        print(f"Email successfully sent to {recipient_email}")
        return "Email sent successfully!", 200
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return f"Error: {str(e)}", 500


@app.route("/triage_results")
def triage_results():
    # Fetch from query parameters
    patient_id = request.args.get('patient_id', 'Not Available')
    name = request.args.get('name', 'Not Available')
    age = request.args.get('age', 'Not Available')
    gender = request.args.get('gender', 'Not Available')
    contact = request.args.get('contact', 'Not Available')
    symptoms = request.args.get('symptoms', 'Not Available')
    history = request.args.get('history', '')
    triage = request.args.get('triage', '')
    specialization = request.args.get('specialization', '')
    doctor = request.args.get('doctor', '')
    appointment_date = request.args.get('date', '')
    appointment_time = request.args.get('time', '')
    wait = request.args.get('wait', '')

    # Render the triage results page with the values
    return render_template("triage_results.html",
                           patient_id=patient_id, name=name, age=age, gender=gender,
                           contact=contact, symptoms=symptoms, history=history,
                           triage=triage, specialization=specialization,
                           doctor=doctor, date=appointment_date, time=appointment_time, wait=wait)


@app.route('/emergency', methods=['GET', 'POST'])
def emergency():
    if request.method == 'POST':
        patient_name = request.form.get('patient_name')
        phone = request.form.get('phone')
        specialization = request.form.get('specialization')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            today = datetime.today().strftime('%A').lower()
            assigned_doctor = None

            # STEP 1: Regular doctor available today & has no appointments
            cursor.execute("""
                SELECT DOCTOR_ID 
                FROM DOCTOR_SCHEDULE
                WHERE SPECIALIZATION = ?
                  AND LOWER(AVAILABLE_DAYS) LIKE ?
                  AND LOWER(AVAILABLE_DAYS) NOT IN ('walkin', 'emergency')
            """, (specialization, f"%{today}%"))
            regular_doctors = cursor.fetchall()

            for doctor in regular_doctors:
                doctor_id = doctor[0]
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM PATIENT_TRIAGE 
                    WHERE ASSIGNED_DOCTOR = ?
                      AND TO_CHAR(APPOINTMENT_DATE, 'YYYY-MM-DD') = TO_CHAR(SYSDATE, 'YYYY-MM-DD')
                """, (doctor_id,))
                if cursor.fetchone()[0] == 0:
                    assigned_doctor = doctor_id
                    break

            # STEP 2: Walk-in doctor with zero appointments
            if not assigned_doctor:
                cursor.execute("""
                    SELECT DOCTOR_ID 
                    FROM DOCTOR_SCHEDULE 
                    WHERE SPECIALIZATION = ?
                      AND LOWER(AVAILABLE_DAYS) = 'walkin'
                """, (specialization,))
                walkin_doctors = cursor.fetchall()

                for doctor in walkin_doctors:
                    doctor_id = doctor[0]
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM PATIENT_TRIAGE 
                        WHERE ASSIGNED_DOCTOR = ?
                          AND TO_CHAR(APPOINTMENT_DATE, 'YYYY-MM-DD') = TO_CHAR(SYSDATE, 'YYYY-MM-DD')
                    """, (doctor_id,))
                    if cursor.fetchone()[0] == 0:
                        assigned_doctor = doctor_id
                        break

            # ✅ STEP 3: Emergency doctor (Oracle 11g compatible)
            if not assigned_doctor:
                cursor.execute("""
                    SELECT DOCTOR_ID 
                    FROM DOCTOR_SCHEDULE 
                    WHERE SPECIALIZATION = ?
                      AND LOWER(AVAILABLE_DAYS) = 'emergency'
                      AND ROWNUM = 1
                """, (specialization,))
                emergency_doctor = cursor.fetchone()
                if emergency_doctor:
                    assigned_doctor = emergency_doctor[0]

            # STEP 4: No doctor found
            if not assigned_doctor:
                flash("No doctor is available for emergency handling in this specialization today.", "error")
                return redirect(url_for('emergency'))

            # ✅ Insert into EMERGENCY_QUEUE
            # Insert into EMERGENCY_QUEUE with sequence value for EMERGENCY_ID
            cursor.execute("""
    INSERT INTO EMERGENCY_QUEUE (
        EMERGENCY_ID, PATIENT_NAME, PHONE, SPECIALIZATION, ASSIGNED_DOCTOR
    ) VALUES (EMERGENCY_QUEUE_SEQ.NEXTVAL, ?, ?, ?, ?)
""", (patient_name, phone, specialization, assigned_doctor))

            conn.commit()
            flash(f"Emergency case submitted. Assigned to Doctor ID: {assigned_doctor}", "success")

        except Exception as e:
            flash(f"Database error: {e}", "error")
        finally:
            conn.close()

        return redirect(url_for('emergency'))

    return render_template('emergency.html')


@app.route('/emergency_queue')
def emergency_queue():
    if 'user_id' not in session or session['role'] not in ['Doctor', 'Admin']:
        flash("Unauthorized access!", "error")
        return redirect(url_for('login'))

    status_filter = request.args.get('status', 'all')  # can be 'all' or 'Waiting'

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        base_query = """
            SELECT E.EMERGENCY_ID, E.PATIENT_NAME, E.PHONE, E.SPECIALIZATION,
                   U.NAME AS DOCTOR_NAME, E.REPORTED_AT, E.STATUS
            FROM EMERGENCY_QUEUE E
            JOIN USERS1 U ON E.ASSIGNED_DOCTOR = U.USER_ID
        """
        params = []

        # Filter for doctor or admin
        if session['role'] == 'Doctor':
            base_query += " WHERE E.ASSIGNED_DOCTOR = ?"
            params.append(session['user_id'])

        # Status filtering
        if status_filter == 'Waiting':
            base_query += " AND" if "WHERE" in base_query else " WHERE"
            base_query += " E.STATUS = 'Waiting'"

        base_query += " ORDER BY E.REPORTED_AT ASC"
        cursor.execute(base_query, tuple(params))
        emergency_cases = cursor.fetchall()
    finally:
        conn.close()

    return render_template('emergency_queue.html', cases=emergency_cases, role=session['role'], status_filter=status_filter)



@app.route('/mark_emergency_diagnosed/<int:emergency_id>', methods=['POST'])
def mark_emergency_diagnosed(emergency_id):
    if 'user_id' not in session or session['role'] not in ['Doctor', 'Admin']:
        flash("Unauthorized action!", "error")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if session['role'] == 'Doctor':
            cursor.execute("""
                UPDATE EMERGENCY_QUEUE
                SET STATUS = 'Diagnosed'
                WHERE EMERGENCY_ID = ? AND ASSIGNED_DOCTOR = ?
            """, (emergency_id, session['user_id']))
        else:
            cursor.execute("""
                UPDATE EMERGENCY_QUEUE
                SET STATUS = 'Diagnosed'
                WHERE EMERGENCY_ID = ?
            """, (emergency_id,))
        conn.commit()
        flash("Emergency case marked as diagnosed.", "success")
    except Exception as e:
        flash(f"Error updating status: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for('emergency_queue'))

@app.route('/admin/add_walkin')
def admin_add_walkin():
    if 'role' not in session or session['role'] != 'Admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    return render_template("admin_add_walkin.html")
@app.route('/admin/walkins', methods=['GET', 'POST'])
def admin_walkins():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Your existing POST code to add walk-in
        name = request.form['patient_name']
        age = int(request.form['age'])
        gender = request.form['gender']
        contact = request.form['contact']
        specialization = request.form['specialization']
        symptoms = request.form['symptoms'].lower()
        booking_time = datetime.now()

        # ... triage mapping, assign doctor, etc. (same code you wrote) ...

        triage_mapping = {
            "Cardiology": {"Critical": ["heart attack", "severe chest pain", "cardiac arrest"],
                        "High": ["irregular heartbeat", "shortness of breath"],
                        "Moderate": ["palpitations"],
                        "Low": ["mild fatigue"]},
            "Neurology": {"Critical": ["stroke", "seizure"],
                        "High": ["migraine", "numbness"],
                        "Moderate": ["dizziness"],
                        "Low": ["headache"]},
            "Orthopedics": {"Critical": ["compound fracture"],
                            "High": ["bone fracture"],
                            "Moderate": ["sprain"],
                            "Low": ["minor bruises"]},
            "Pediatrics": {"Critical": ["newborn fever"],
                        "High": ["high fever", "persistent cough"],
                        "Moderate": ["moderate fever"],
                        "Low": ["runny nose"]},
            "General Medicine": {"Critical": ["sepsis", "unconsciousness"],
                                "High": ["severe fatigue", "high fever"],
                                "Moderate": ["cold", "headache"],
                                "Low": ["body aches"]}
        }

        triage_level = "Low"
        for level, keywords in triage_mapping.get(specialization, {}).items():
            if any(keyword in symptoms for keyword in keywords):
                triage_level = level
                break

        cursor.execute("""
    SELECT DOCTOR_ID 
    FROM DOCTOR_SCHEDULE 
    WHERE SPECIALIZATION = ? AND LOWER(AVAILABLE_DAYS) = 'walkin'
    AND ROWNUM = 1
""", (specialization,))

        result = cursor.fetchone()

        if not result:
            flash("No doctor available for this specialization today.", "error")
            conn.close()
            return redirect(url_for('admin_add_walkin'))

        doctor_id = result[0]
        appointment_date = booking_time.date()

        cursor.execute("""
            SELECT TOKEN_NO, TRIAGE_LEVEL, BOOKING_DATETIME
            FROM walkins
            WHERE ASSIGNED_DOCTOR = ? AND APPOINTMENT_DATE = ?
            ORDER BY 
                CASE TRIAGE_LEVEL
                    WHEN 'Critical' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Moderate' THEN 3
                    WHEN 'Low' THEN 4
                END,
                BOOKING_DATETIME ASC
        """, (doctor_id, appointment_date))

        existing = cursor.fetchall()

        start_time = datetime.strptime("09:00", "%H:%M")
        first_time = start_time

        if existing:
            token, level, _ = existing[0]
            increment = 15 if level in ("High", "Critical") else 10
            start_time += timedelta(minutes=increment)

            for token, level, _ in existing[1:]:
                increment = 15 if level in ("High", "Critical") else 10
                start_time += timedelta(minutes=increment)

        appointment_time = start_time.strftime("%I:%M %p")
        wait_min = int((start_time - first_time).total_seconds() // 60)
        wait_text = f"{wait_min} mins" if wait_min > 0 else "Immediate"

        cursor.execute("SELECT NVL(MAX(TOKEN_NO), 0) + 1 FROM walkins")
        token_no = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO walkins (
                TOKEN_NO, PATIENT_NAME, AGE, GENDER, CONTACT, SYMPTOMS,
                SPECIALIZATION, TRIAGE_LEVEL, ASSIGNED_DOCTOR,
                APPOINTMENT_DATE, APPOINTMENT_TIME, ESTIMATED_WAITING_TIME,
                STATUS, BOOKING_DATETIME
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Waiting', ?)
        """, (
            token_no, name, age, gender, contact, symptoms,
            specialization, triage_level, doctor_id,
            appointment_date, appointment_time, wait_text,
            booking_time
        ))

        conn.commit()
        flash(f"Walk-in added: {name}, {triage_level} level at {appointment_time}", "success")
        conn.close()
        return redirect(url_for('admin_walkins'))

    else:
        # GET request: fetch walk-ins with doctor names
        cursor.execute("""
            SELECT 
                W.TOKEN_NO, W.PATIENT_NAME, W.AGE, W.GENDER, W.SYMPTOMS, 
                W.SPECIALIZATION, U.NAME AS DOCTOR_NAME, 
                W.APPOINTMENT_DATE, W.TRIAGE_LEVEL
            FROM walkins W
            LEFT JOIN USERS1 U ON W.ASSIGNED_DOCTOR = U.USER_ID
            ORDER BY W.TOKEN_NO ASC
        """)

        walkins = cursor.fetchall()
        conn.close()
        walkins_list = []

        for row in walkins:
            # Convert row tuple to list so it's mutable
            row = list(row)

            # Convert APPOINTMENT_DATE (index 7) to datetime.date if it's a string
            if isinstance(row[7], str):
                try:
                    row[7] = datetime.strptime(row[7], '%Y-%m-%d').date()
                except Exception as e:
                    print(f"Date conversion error: {e}")
                    # Keep original if conversion fails

            # Append modified row back to list
            walkins_list.append(row)

        
        return render_template('admin_walkins.html',walkins=walkins_list)
from datetime import datetime, timedelta
from flask import request, redirect, url_for, flash

from datetime import datetime, timedelta
import uuid  # Add this import at the top of your file if not already present

@app.route('/admin/cancel_appointment', methods=['POST'])
def admin_cancel_appointment():
    patient_id = request.form.get("patient_id")
    specialization = request.form.get("specialization")
    appointment_date = request.form.get("appointment_date")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Step 1: Get doctor_id of the patient being cancelled
        cursor.execute("""
            SELECT ASSIGNED_DOCTOR FROM PATIENT_TRIAGE
            WHERE PATIENT_ID = ? AND SPECIALIZATION = ? AND TO_CHAR(APPOINTMENT_DATE, 'YYYY-MM-DD') = ?
        """, (patient_id, specialization, appointment_date))
        result = cursor.fetchone()

        if not result:
            flash("Patient not found or already cancelled.", "error")
            return redirect(url_for('admin_dashboard'))

        doctor_id = result[0]
        print("🩺 Cancelled patient's doctor ID:", doctor_id)

        # Step 2: Mark patient as cancelled
        cursor.execute("""
            UPDATE PATIENT_TRIAGE
            SET STATUS = 'Cancelled'
            WHERE PATIENT_ID = ? AND SPECIALIZATION = ? AND TO_CHAR(APPOINTMENT_DATE, 'YYYY-MM-DD') = ?
        """, (patient_id, specialization, appointment_date))

        # Step 3: Find a walk-in to promote
        cursor.execute("""
    SELECT * FROM (
        SELECT * FROM walkins
        WHERE SPECIALIZATION = ?
          AND TO_CHAR(APPOINTMENT_DATE, 'YYYY-MM-DD') = ?
        ORDER BY 
            CASE TRIAGE_LEVEL
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Moderate' THEN 3
                WHEN 'Low' THEN 4
            END,
            BOOKING_DATETIME ASC
    ) WHERE ROWNUM = 1
""", (specialization, appointment_date))


        walkin = cursor.fetchone()

        if walkin:
            # Unpack walk-in data (ensure this matches your actual column order)
            (token_no, name, age, gender, contact, symptoms,
             spec, triage_level, _, appt_date,
             _, _, _, booking_time) = walkin

            # Step 3.1: Check if this walk-in already exists in PATIENT_TRIAGE
            cursor.execute("""
                SELECT 1 FROM PATIENT_TRIAGE
                WHERE CONTACT = ? 
                AND DBMS_LOB.SUBSTR(SYMPTOMS, 4000, 1) = ? 
                AND TO_CHAR(APPOINTMENT_DATE, 'YYYY-MM-DD') = ?
            """, (contact, symptoms, appointment_date))
            
            if cursor.fetchone():
                flash("This walk-in is already assigned to a doctor.", "warning")
                return redirect(url_for('admin_dashboard'))

            # Step 3.2: Generate a unique patient ID
            unique_suffix = uuid.uuid4().hex[:6]
            max_pid_length = 10
            prefix = f"W{token_no}_"
            available_length = max_pid_length - len(prefix)
            trimmed_suffix = unique_suffix[:available_length]
            new_pid = prefix + trimmed_suffix

            print(f"✅ Promoting walk-in '{name}' (Token {token_no}) to doctor '{doctor_id}' with ID {new_pid}")

            # Step 3.3: Insert into PATIENT_TRIAGE
            cursor.execute("""
                INSERT INTO PATIENT_TRIAGE (
                    PATIENT_ID, NAME, AGE, GENDER, CONTACT, SYMPTOMS, SPECIALIZATION,
                    TRIAGE_LEVEL, ASSIGNED_DOCTOR, STATUS, BOOKING_DATETIME, APPOINTMENT_DATE
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, TO_DATE(?, 'YYYY-MM-DD'))
            """, (
                new_pid, name, age, gender, contact, symptoms, specialization,
                triage_level, doctor_id,
                booking_time, appointment_date
            ))

            # Step 3.4: Delete the walk-in from walkins table
            cursor.execute("DELETE FROM walkins WHERE TOKEN_NO = ?", (token_no,))
        else:
            print("⚠️ No walk-in patient found for specialization:", specialization)

        # Step 4: Recalculate the queue for the doctor
        cursor.execute("""
            SELECT PATIENT_ID, TRIAGE_LEVEL, TO_CHAR(BOOKING_DATETIME, 'YYYY-MM-DD HH24:MI:SS')
            FROM PATIENT_TRIAGE
            WHERE ASSIGNED_DOCTOR = ?
              AND TO_CHAR(APPOINTMENT_DATE, 'YYYY-MM-DD') = ?
              AND STATUS = 'Pending'
            ORDER BY 
                CASE TRIAGE_LEVEL
                    WHEN 'Critical' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Moderate' THEN 3
                    WHEN 'Low' THEN 4
                END,
                BOOKING_DATETIME ASC
        """, (doctor_id, appointment_date))

        patients = cursor.fetchall()
        current_time = datetime.strptime("09:00", "%H:%M")
        first_time = current_time

        for pid, level, _ in patients:
            appt_time = current_time.strftime("%I:%M %p")
            wait_min = int((current_time - first_time).total_seconds() // 60)
            wait_text = f"{wait_min} mins" if wait_min > 0 else "Immediate"

            cursor.execute("""
                UPDATE PATIENT_TRIAGE
                SET APPOINTMENT_TIME = ?, ESTIMATED_WAITING_TIME = ?
                WHERE PATIENT_ID = ?
            """, (appt_time, wait_text, pid))

            increment = 15 if level in ("High", "Critical") else 10
            current_time += timedelta(minutes=increment)

        conn.commit()
        flash("Appointment cancelled. Walk-in assigned and queue updated.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error during cancellation: {e}", "error")
        print(f"[ERROR] {e}")

    finally:
        conn.close()

    return redirect(url_for('admin_dashboard'))

# =======================
# 🔹 Run Flask App
# =======================

if __name__ == '__main__':
    app.run(debug=True)


