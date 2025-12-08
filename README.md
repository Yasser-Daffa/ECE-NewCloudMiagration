# ECE Course Registration System  
**Team A — EE202 OOB Final Project**

A full university course-registration system built with **Python, PyQt6, and PostgreSQL**.  
Originally developed using a **local SQLite database**, later fully migrated to **Supabase (PostgreSQL)** with cloud pooling, connection retries, and session-safe database utilities.

This system includes complete dashboards for **Students** and **Admins**, cloud-synced authentication, prerequisite checking, study plans, transcript generation, and real-time connection status monitoring.


Honesty: This project wouldn't have been possible to make in such a short period of time (1.5 months) without the help of ChatGPT <3
---

# Features Overview

### Student Dashboard
- View current schedule  
- Register courses with prerequisite & seat validation (section capacity)
- View degree/program plan & program prerequisites
- View completed courses, grades, and transcript  
- Profile management with email verification  
 

### Admin Dashboard
- Manage students, faculty, courses, sections, grades  
- Approve or reject new student accounts  
- Set program study plans and ability to edit them  
- Set prerequisites for each course  
- View system statistics (partially implemented)

### Shared between the two dashboards
- Real-time cloud-connection indicator
- Powerful sign-in/account creation window
- Neat looking design
- Clean UI
- Made with love (and a loss of mental sanity)



---

# Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | PyQt6 (custom UI, animations, stacked widgets) |
| **Backend** | Python 3.13+ |
| **Database (Cloud)** | Supabase PostgreSQL (Free Tier) |
| **Local DB (Initial)** | SQLite |
| **Security** | bcrypt password hashing, email verification |
| **Architecture** | Multi-window MVC* with shared utilities |

MVC*: model view controller

---

# Database Migration Notes (SQLite -> Cloud PostgreSQL)

### Why We Migrated
The original design ran on SQLite and worked locally, but had issues:
- No concurrency support  
- No remote access  
- No real multi-user capability  
- Only one person can access the local .db file at a time. else it would result in a coruption due to the file's binary nature
- Caused us emotional damage during testing

### Migration Steps
1. **Rewrote SQL schemas** to match PostgreSQL's structure.  
2. **Replaced sqlite3 syntax** with **psycopg2 + Supabase connection pooling**.  
3. Added:
   - Connection retry logic (3 attempts)
   - Pooled connections for the entire app lifecycle
   - Automatic reconnection after dropped sessions  
4. Updated all database utility methods to:
   - Accept a shared pool connection  
   - Never open new connections per method  
   - Keep consistent naming to avoid breaking UI logic  
5. Reworked authentication & email verification to fully support cloud workflows.

### Cloud Challenges Solved
- PostgreSQL session mode limits (MaxClientsInSessionMode errors)
- Excessive connection creation -> fixed using a **single shared pool**  
- Query timeouts -> resolved with shorter, optimized SELECTs  
- Real-time "Online/Offline" monitoring
- Dead sessions... session would die after 4 mins of inactivity (had to write a method to reconnect safely)
- ^^^^^^^^^^^^^^^ This part in particular was a headache to figure out. "WHY IS THE PROGRAM CRASHING AFTER A 2 SECONDS OF NOT USING IT"

---

# System Architecture

app/
│
├── login_files/ # Authentication system (student/admin login)
│ ├── class_authentication_window.py
│ └── email verification, password reset, stacked UI
│
├── student/
│ ├── class_student_dashboard.py
│ ├── submenus/ # Profile, schedule, program plans, transcript, etc.
│ └── class_student_utilities.py
│
├── admin/
│ ├── class_admin_dashboard.py
│ ├── submenus/ # Manage courses, sections, students, grades, etc.
│ └── class_admin_utilities.py
│
├── database_files/
│ ├── cloud_database.py # Pooled connection, retry logic
│ ├── class_database_uitlities.py
│ └── migrated SQL schemas
│
└── helper_files/
   ├── shared_utilities.py # Common UI helpers
   ├── validators.py # Password hashing, input validation
   └── email_sender.py


---

# Installation (User)

### 1. Download the release folder  
go to `dir` folder -> then `output`.
Inside it you will a **setup file**. download the latest one always, as it has the most recent bug fixes

Example path:
dir/output_v2/setup.exe
 - *download this* ----- ^^^^^

### 2. Run:
launch the **setup.exe** file and proceed normally

---

# Setting Up Your Own Cloud Database (Supabase PostgreSQL)

If you want to host your own version of this project, follow these steps to create your own cloud database instead of using the included configuration.

---

## 0. Requirements
Before starting, make sure you have:

- Python 3.13+ installed
- A code editor (VS Code, PyCharm, etc.)
- Internet connection
- The following Python packages installed:

   - pip install python-dotenv psycopg2

   - pip install bcrypt

   - pip install smtplib


---

## 1. Create a Supabase Account
1. Visit https://supabase.com  
2. Sign up (GitHub or email is fine)
3. Click **New Project**

Make sure you select:

- **PostgreSQL database**
- A **Region close to you**  
- **Free Plan** (more than enough for this project)

---

## 2. Get Your Database Credentials

Inside your Supabase project:

1. Go to **Project Settings**
2. Click **Database**
3. Scroll down to **Connection Info**
4. Copy the following values:

- `host`
- `password`
- `port` (usually 5432)
- `database`
- `user`

You will paste these into the project in the next step.

---

## 3. Configure the Project to Use Your Database

1. Download this repository; <> Code -> then Download ZIP  
2. Extract it  
3. Open the folder in your IDE  
4. Go to:

database_files/cloud_database.py


5. Find these lines:

```python
SUPABASE_HOST = ""
SUPABASE_USER = ""
SUPABASE_PASSWORD = ""

SUPABASE_DB = ""

5. Replace them with your actual credentials from Supabase:
Example:
    SUPABASE_HOST = "aws-xyz-123.supabase.co"
    SUPABASE_USER = "postgres"
    SUPABASE_PASSWORD = "your_real_password"
    SUPABASE_DB = "postgres"
```
    
---

## 4. Initialize the Database Tables

- Inside Supabase:

   1. Go to the SQL Editor

   2. Copy the schema located in:

database_files/schemas/supabase_schema.sql

   3. Paste it into Supabase’s SQL editor

   4. Run it

   5. This will automatically create all tables, foreign keys, indexes, and relationships needed for the system.

If you want to reset the database at any time, simply re-run the schema file.




# Contributors (Team A)

| Name         | Role                                         |
| ------------ | -------------------------------------------- |
| Yasser       | Project Lead, GUI development, Cloud Migration, GUI ↔ Backend connection |
| Salim        | Backend Logic (Database setup, Admin Class), GUI ↔ Backend connection |
| Ahmed        | Backend Logic (Database setup, Student Class, Cloud Migration) |
| Mohanned     | Email/Username/ID Authenticators, Error handling/Testing |
| Yehya        | Password Authenticators, Error handling/Testing|
