import sqlite3
import re
import os
import sys
from flask_bcrypt import Bcrypt

# --- Student roll numbers use the format ENG<yy><branch><4 digits>, e.g. ENG25AD0154 ---
# Branch codes: CS, AI, AD (AI & Data Science), EC, EA, ME
STUDENT_DATA = [
    ("ENG25CS0001", "ABHUITH NAMBIAR", "Male", "Computer Science and Engineering", "A", "E208"),
    ("ENG25CS0002", "ADITI SINGHAL", "Female", "Computer Science and Engineering", "A", "E208"),
    ("ENG25CS0003", "Akhila T", "Female", "Computer Science and Engineering", "A", "E208"),
    ("ENG25CS0004", "Bhuvana V Sharma", "Female", "Computer Science and Engineering", "A", "E208"),
    ("ENG25CS0005", "BONTHU PAVAN", "Male", "Computer Science and Engineering", "A", "E208"),
    ("ENG25CS0006", "BUDUMURU VAISHNAVI", "Female", "Computer Science and Engineering", "A", "E208"),
    ("ENG25CS0007", "BUTHAM HARSHAVARDHAN", "Male", "Computer Science and Engineering", "A", "E208"),
    ("ENG25CS0008", "CHALUVADI JYOTHIKA", "Female", "Computer Science and Engineering", "A", "E208"),
    ("ENG25CS0009", "CHILLAKURU CHATRESH REDDY", "Male", "Computer Science and Engineering", "A", "E208"),
    ("ENG25CS0010", "DAYADI ABHUITH", "Male", "Computer Science and Engineering", "A", "E208"),
    ("ENG25AI0001", "Abhinav Rajesh", "Male", "Computer Science and Engineering (AI)", "D", "A108"),
    ("ENG25AI0002", "ABHIRAM ARUNN SV", "Male", "Computer Science and Engineering (AI)", "D", "A108"),
    ("ENG25AI0003", "ACHUTHA LOKANATHA VIGHNESH", "Male", "Computer Science and Engineering (AI)", "D", "A108"),
    ("ENG25AD0154", "Abhinav CK", "Male", "Artificial Intelligence and Data Science", "G", "B 108"),
    ("ENG25AD0155", "ADUDHODLA RANVITHA REDDY", "Female", "Artificial Intelligence and Data Science", "G", "B 108"),
    ("ENG25EC0001", "AARIKATLA REETHIKA", "Female", "Electronics and Communication Engineering", "H", "E205"),
    ("ENG25EC0002", "ACHANTA HEMA RATNA SAI SUBBARAO", "Male", "Electronics and Communication Engineering", "H", "E205"),
    ("ENG25EA0001", "Adithya M D", "Male", "Electronics and Computer Engineering", "K", "E-Learning Hall"),
    ("ENG25EA0002", "AKUTHOTA POOJITHA", "Female", "Electronics and Computer Engineering", "K", "E-Learning Hall"),
    ("ENG25ME0001", "A BADRINATH", "Male", "Mechanical Engineering", "N", "B107"),
    ("ENG25ME0002", "Aayush Jayachandran", "Male", "Mechanical Engineering", "N", "B107")
]

# No demo faculty on purpose: every faculty member creates their own account on the signup page
# (using the faculty access code), so there is no shared password.

def roll_to_email(roll_no):
    """ENG25AD0154 -> Eng25ad0154@dsu.edu.in"""
    return roll_no.strip().capitalize() + "@dsu.edu.in"

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'project_tracker.db')

def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    bcrypt = Bcrypt()

    # Drop tables if they exist for a clean setup
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS students")
    cursor.execute("DROP TABLE IF EXISTS faculty")
    cursor.execute("DROP TABLE IF EXISTS projects")
    cursor.execute("DROP TABLE IF EXISTS project_members")
    cursor.execute("DROP TABLE IF EXISTS tasks")
    cursor.execute("DROP TABLE IF EXISTS feedback")
    
    # --- Create Tables ---
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE students (
            user_id INTEGER PRIMARY KEY,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            gender TEXT,
            specialization TEXT,
            section TEXT,
            classroom_number TEXT,
            email TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE faculty (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT,
            email TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # In database.py

    cursor.execute('''
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            faculty_id INTEGER,
            department TEXT,
            status TEXT NOT NULL,
            submission_date TEXT,
            progress_percentage INTEGER DEFAULT 0, -- <<< ADD THIS LINE
            FOREIGN KEY(faculty_id) REFERENCES faculty(user_id)
        )
    ''')
    

    cursor.execute('''
        CREATE TABLE project_members (
            project_id INTEGER,
            student_id INTEGER,
            PRIMARY KEY (project_id, student_id),
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(student_id) REFERENCES students(user_id)
        )
    ''')
    
   # In database.py

    cursor.execute('''
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            student_id INTEGER, -- Who submitted the work
            title TEXT NOT NULL,
            description TEXT,
            progress_description TEXT, -- Student's description of work
            file_path TEXT,
            status TEXT NOT NULL, -- e.g., 'assigned', 'pending_approval', 'approved'
            percentage_value INTEGER DEFAULT 0, -- <<< ADD THIS LINE (Weight of the task)
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(student_id) REFERENCES students(user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            faculty_id INTEGER,
            feedback_text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(faculty_id) REFERENCES faculty(user_id)
        )
    ''')
    
    print("Tables created successfully.")
    
    # --- Populate ONLY Users (Students and Faculty) ---
    hashed_password = bcrypt.generate_password_hash("password123").decode('utf-8')
    
    for roll_no, name, gender, spec, section, room in STUDENT_DATA:
        clean_roll = re.sub(r'[\s\.]', '', roll_no).upper()
        email = roll_to_email(clean_roll)
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'student')", (clean_roll, hashed_password))
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO students (user_id, roll_no, name, gender, specialization, section, classroom_number, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(user_id, clean_roll, name, gender, spec, section, room, email))
    print(f"{len(STUDENT_DATA)} students inserted.")
    
    conn.commit()
    conn.close()
    print("\nDatabase created with demo students only. Faculty must sign up with the faculty access code. No default projects were added.")

if __name__ == '__main__':
    # create_database() DROPS all tables, so refuse to run on an existing DB unless asked.
    def _has_data():
        if not os.path.exists(DB_PATH):
            return False
        try:
            c = sqlite3.connect(DB_PATH)
            found = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
            c.close()
            return found is not None
        except sqlite3.Error:
            return False

    if _has_data() and '--reset' not in sys.argv:
        print("project_tracker.db already exists. Running this would ERASE all data.")
        print("If you really want that, run:  python database.py --reset")
        sys.exit(1)
    create_database()
    print("\nSample Student Login:")
    print("Username: ENG25AD0154")
    print("Password: password123")
    print("\nFaculty: create an account on the Create account page (needs the faculty access code).")
