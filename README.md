# 🏥 Patient Management System (Flask + Oracle DB)

A full-stack **Flask-based web application** to manage patient triage, appointment booking, emergency handling, diagnosis, and user roles like Admin, Doctor, and Patient. This application integrates **email notifications** and enforces business logic like **appointment limits** and **prioritization based on triage levels**.

---

## 📌 Features

### 🧑‍⚕️ Role-based Login System
- **Admin**: Manage appointments, walk-ins, and doctor schedules.
- **Doctor**: View assigned patients, diagnose, and manage availability.
- **Patient**: Book appointments, view queue, triage, and history.

### 📋 Patient Triage System
- Automatically determines triage level (Critical, High, Moderate, Low) based on symptoms and specialization.
- Assigns doctors intelligently based on availability and workload.
- Implements appointment slotting logic and prioritization.

### 🚑 Emergency Handling
- Supports emergency and walk-in appointments.
- Auto-assigns doctors based on specialization and available schedules.
- Maintains a separate queue for emergency patients.

### 🕒 Time Slot Management
- Dynamic time slot generation based on appointment load and triage level.
- **Max 12 patients per doctor per day**.
- Automatic reassignment and rescheduling logic after cancellations.

### 📧 Email Notifications
- Sends appointment details to patients via email using **Flask-Mail**.

### 📄 Admin Dashboard
- View all pending appointments and emergency cases.
- Promote walk-in patients into the regular queue automatically.
- Cancel/reschedule appointments.

---

## 🧰 Tech Stack

| Layer      | Technology                   |
|------------|------------------------------|
| Backend    | Python, Flask                |
| Frontend   | HTML, CSS (Jinja2 Templates) |
| Database   | Oracle (via pyodbc)          |
| Email      | Flask-Mail, Gmail SMTP       |
| Env Vars   | python-dotenv                |

---

## 📁 Project Structure
```
project/
│
├── app.py # Main Flask application
├── requirements.txt # Project dependencies
├── .env # Environment variables (e.g., Gmail credentials)
├── templates/ # HTML templates (login, dashboard, forms)
├── static/ # CSS/JS/image assets
└── README.md # Project documentation
```

---

## 🔐 Environment Variables

Create a `.env` file in your project root with the following content:

```env
GMAIL_USERNAME=your_username
GMAIL_PASSWORD=your_app_password
```
⚠️ Use Gmail App Passwords if you have 2FA enabled.

---

## 🧪 How to Run Locally

### Clone the repository

```
git clone https://github.com/YOUR_USERNAME/patient-management-system.git
cd patient-management-system
```
### Create and activate virtual environment
```
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```
### Install dependencies
```
pip install -r requirements.txt
Set up .env file
```
Add your Gmail credentials to the .env file.

### Run the app

```
python app.py
```
Visit the application in your browser at: http://127.0.0.1:5000

---

## 🧑‍💻 Database Assumptions

This application is designed to work with an **Oracle Database**.

### ✅ Required Tables
Ensure your Oracle DB includes the following tables:

|Table Name    	|Description  |
|---------------|-------------|
|USERS1	| Stores user credentials and roles (Admin, Doctor, Patient) |
|PATIENT_TRIAGE	 | Contains triage records, appointment scheduling, symptoms|
|PPD	 | Stores diagnosis and prescription data|
|DOCTOR_SCHEDULE	| Maintains doctor availability and specialization |
|EMERGENCY_QUEUE | Queue for emergency cases needing immediate attention |
|WALKINS | Temporary table for walk-in patients before promotion|

⚠️ Ensure these tables are created with appropriate fields and data types before running the app.

---

## ✅ ODBC Connection

The app uses pyodbc to connect to Oracle via a DSN (Data Source Name).

Sample connection string:
```
ODBC_CONNECTION_STRING = "DSN=user_dns_name;Uid=database_name;Pwd=password;"
```
Replace with actual credentials securely via .env in production.

---
## 🙌 Contributions

Feel free to open issues or submit pull requests to improve the project.

---

## 👤 Author

**Sri**  
B.Tech Information Technology    
[LinkedIn]([https://www.linkedin.com/in/your-username/](https://www.linkedin.com/in/rajasri-sampath-kumar-892046296/)) | [GitHub](https://github.com/Rajasri-1406)

---

## 📄 License

This project is licensed under the MIT License.

Let me know if you'd like to include:
- Screenshots
- Sample `.sql` file to create tables
- Docker support
- GitHub Pages documentation

I'll help generate those too!
