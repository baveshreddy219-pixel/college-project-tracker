import sqlite3
import re
import os
import hmac
from flask import Flask, jsonify, request, render_template, g, send_from_directory
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# --- App Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'docx', 'pptx'}

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-me')
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'

DATABASE = os.path.join(BASE_DIR, 'project_tracker.db')

# Make sure the uploads folder exists (needed when run by a web server, not just __main__)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Faculty access code ---
# Only people who know this code can register as faculty. Give it privately to real faculty.
# CHANGE IT: either edit the text below, or (better) set the FACULTY_CODE environment variable on your server.
FACULTY_CODE = os.environ.get('FACULTY_CODE', 'DSU-FACULTY-2026')

# --- Roll number / email format ---
# Roll no: ENG + 2-digit year + 2-letter branch + 4 digits   e.g. ENG25AD0154
# Email:   Eng25ad0154@dsu.edu.in
ROLL_RE = re.compile(r'ENG\d{2}[A-Z]{2}\d{4}')
EMAIL_DOMAIN = '@dsu.edu.in'

def roll_to_email(roll_no):
    return roll_no.capitalize() + EMAIL_DOMAIN

def normalize_username(raw):
    """Strip spaces/dots, upper-case. Accepts the college email too (Eng25ad0154@dsu.edu.in)."""
    raw = (raw or '').strip()
    if raw.lower().endswith(EMAIL_DOMAIN):
        raw = raw[:-len(EMAIL_DOMAIN)]
    return re.sub(r'[\s\.]', '', raw).upper()

def _squash(text):
    """'Dr. Smith' and 'Dr.Smith' and 'dr smith' all become 'drsmith'."""
    return re.sub(r'[\s\.]', '', (text or '')).lower()

def find_faculty(db, query):
    """Find one faculty member from what a student typed: their email or their name.
    Returns (user_id, None) on success or (None, error_message)."""
    query = (query or '').strip()
    if not query:
        return None, "Enter your faculty guide's email or name."
    rows = db.execute("SELECT user_id, name, email FROM faculty").fetchall()
    by_email = [r for r in rows if (r['email'] or '').strip().lower() == query.lower()]
    if len(by_email) == 1:
        return by_email[0]['user_id'], None
    by_name = [r for r in rows if _squash(r['name']) == _squash(query)]
    if len(by_name) == 1:
        return by_name[0]['user_id'], None
    if len(by_name) > 1:
        return None, "More than one faculty has that name. Please enter their email address instead."
    return None, "No faculty found with that name or email. Ask your guide to create a faculty account first."

# --- Helper Function ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Database Connection ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- User Authentication ---
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cursor = db.cursor()
    user_data = cursor.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,)).fetchone()
    if user_data:
        return User(id=user_data['id'], username=user_data['username'], role=user_data['role'])
    return None

# --- HTML Serving Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/student-dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return "Unauthorized", 403
    return render_template('student-dashboard.html')

@app.route('/faculty-dashboard')
@login_required
def faculty_dashboard():
    if current_user.role != 'faculty':
        return "Unauthorized", 403
    return render_template('faculty-dashboard.html')

# --- API Routes ---
@app.route('/api/login', methods=['POST'])
def handle_login():
    data = request.get_json()
    username = normalize_username(data.get('username'))
    password = data.get('password') or ''
    db = get_db()
    cursor = db.cursor()
    user_data = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user_data and bcrypt.check_password_hash(user_data['password'], password):
        user = User(id=user_data['id'], username=user_data['username'], role=user_data['role'])
        login_user(user)
        return jsonify({"success": True, "role": user_data['role']})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/api/signup', methods=['POST'])
def handle_signup():
    d = request.get_json(silent=True) or {}
    role = d.get('role')
    name = (d.get('name') or '').strip()
    username = normalize_username(d.get('username'))
    password = d.get('password') or ''
    email = (d.get('email') or '').strip()
    dept = (d.get('department') or '').strip()
    def bad(msg, code=400): return jsonify({"success": False, "message": msg}), code
    if role not in ('student', 'faculty'): return bad("Choose Student or Faculty.")
    if not name: return bad("Enter your full name.")
    if role == 'student':
        if not ROLL_RE.fullmatch(username): return bad("Registration number must look like ENG25AD0154.")
        email = roll_to_email(username)   # always derived from the roll number
    else:
        if not re.fullmatch(r'[A-Z0-9_]{4,25}', username): return bad("Username must be 4-25 letters or numbers.")
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email): return bad("Enter a valid email address.")
        email = email.lower()
    if len(password) < 6: return bad("Password must be at least 6 characters.")
    if role == 'faculty' and not hmac.compare_digest((d.get('access_code') or '').strip().encode(), FACULTY_CODE.encode()):
        return bad("Incorrect faculty access code.", 403)
    db = get_db()
    cur = db.cursor()
    if role == 'faculty' and cur.execute("SELECT 1 FROM faculty WHERE lower(email) = ?", (email,)).fetchone():
        return bad("A faculty account with that email already exists. Try signing in.", 409)
    if cur.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
        return bad("That username is already registered. Try signing in.", 409)
    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed, role))
    uid = cur.lastrowid
    if role == 'student':
        cur.execute("INSERT INTO students (user_id, roll_no, name, gender, specialization, section, classroom_number, email) VALUES (?, ?, ?, '', ?, '', '', ?)", (uid, username, name, dept, email))
    else:
        cur.execute("INSERT INTO faculty (user_id, name, department, email) VALUES (?, ?, ?, ?)", (uid, name, dept, email))
    db.commit()
    return jsonify({"success": True, "role": role})

@app.route('/api/logout', methods=['POST'])
@login_required
def handle_logout():
    logout_user()
    return jsonify({"success": True})

# --- Student API Routes ---
@app.route('/api/student/profile')
@login_required
def get_student_profile():
    db = get_db()
    cursor = db.cursor()
    profile_data = cursor.execute("SELECT * FROM students WHERE user_id = ?", (current_user.id,)).fetchone()
    projects = cursor.execute('SELECT p.title, p.status FROM projects p JOIN project_members pm ON p.id = pm.project_id WHERE pm.student_id = ?', (current_user.id,)).fetchall()
    return jsonify({"profile": dict(profile_data), "projects": [dict(p) for p in projects]})

@app.route('/api/student/task/<int:task_id>/submit', methods=['POST'])
@login_required
def submit_work_for_task(task_id):
    file_path = None
    if 'submissionFile' in request.files:
        file = request.files['submissionFile']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_path = filename
        elif file.filename != '':
            return jsonify({"success": False, "message": "File type not allowed"}), 400
    
    data = request.form
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        UPDATE tasks 
        SET student_id = ?, progress_description = ?, file_path = ?, status = 'pending_approval', submitted_at = CURRENT_TIMESTAMP
        WHERE id = ? AND (status = 'assigned' OR status = 'rejected')
    ''', (current_user.id, data['progress_description'], file_path, task_id))

    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"success": False, "message": "Task not found or already submitted."}), 404

    return jsonify({"success": True, "message": "Work submitted for approval."})

@app.route('/api/student/dashboard-stats')
@login_required
def get_student_dashboard_stats():
    if current_user.role != 'student':
        return "Unauthorized", 403
    
    db = get_db()
    cursor = db.cursor()
    
    projects = cursor.execute('''
        SELECT status, progress_percentage FROM projects p
        JOIN project_members pm ON p.id = pm.project_id
        WHERE pm.student_id = ? AND p.status = 'approved'
    ''', (current_user.id,)).fetchall()
    
    total_projects = len(projects)
    completed_projects = 0
    ongoing_projects = 0

    for project in projects:
        if project['progress_percentage'] >= 100:
            completed_projects += 1
        else:
            ongoing_projects += 1
            
    return jsonify({
        "total_projects": total_projects,
        "completed_projects": completed_projects,
        "ongoing_projects": ongoing_projects
    })

@app.route('/api/student/projects', methods=['GET', 'POST'])
@login_required
def handle_student_projects():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        data = request.get_json()
        faculty_id, err = find_faculty(db, data.get('faculty'))
        if err: return jsonify({"success": False, "message": err}), 400
        cursor.execute('INSERT INTO projects (title, description, faculty_id, department, status) VALUES (?, ?, ?, ?, ?)', (data['title'], data['description'], faculty_id, data['department'], 'pending'))
        project_id = cursor.lastrowid
        cursor.execute('INSERT INTO project_members (project_id, student_id) VALUES (?, ?)', (project_id, current_user.id))
        if 'teamMembers' in data and data['teamMembers']:
            teammate_roll_nos = [roll.strip().upper() for roll in data['teamMembers'].split(',')]
            for roll_no in teammate_roll_nos:
                student_user = cursor.execute("SELECT user_id FROM students WHERE roll_no = ?", (roll_no,)).fetchone()
                if student_user:
                    cursor.execute("INSERT OR IGNORE INTO project_members (project_id, student_id) VALUES (?, ?)", (project_id, student_user['user_id']))
        db.commit()
        return jsonify({"success": True, "message": "Project created successfully"})
    projects = cursor.execute('SELECT p.*, f.name as faculty_name FROM projects p JOIN project_members pm ON p.id = pm.project_id JOIN faculty f ON p.faculty_id = f.user_id WHERE pm.student_id = ?', (current_user.id,)).fetchall()
    return jsonify([dict(p) for p in projects])

@app.route('/api/student/feedback')
@login_required
def get_student_feedback():
    if current_user.role != 'student':
        return "Unauthorized", 403
    
    db = get_db()
    cursor = db.cursor()
    
    feedback_data = cursor.execute('''
        SELECT 
            f.feedback_text,
            f.created_at,
            p.title as project_title,
            fac.name as faculty_name
        FROM feedback f
        JOIN projects p ON f.project_id = p.id
        JOIN faculty fac ON f.faculty_id = fac.user_id
        JOIN project_members pm ON p.id = pm.project_id
        WHERE pm.student_id = ?
        ORDER BY f.created_at DESC
    ''', (current_user.id,)).fetchall()

    return jsonify([dict(fb) for fb in feedback_data])

@app.route('/api/student/calendar-deadlines')
@login_required
def get_calendar_deadlines():
    db = get_db()
    cursor = db.cursor()
    deadlines = cursor.execute('''
        SELECT p.title, p.submission_date FROM projects p
        JOIN project_members pm ON p.id = pm.project_id
        WHERE pm.student_id = ? AND p.submission_date IS NOT NULL
    ''', (current_user.id,)).fetchall()
    
    return jsonify([dict(d) for d in deadlines])

# --- Faculty API Routes ---
@app.route('/api/faculty/profile')
@login_required
def get_faculty_profile():
    db = get_db()
    cursor = db.cursor()
    profile_data = cursor.execute("SELECT * FROM faculty WHERE user_id = ?", (current_user.id,)).fetchone()
    projects = cursor.execute("SELECT title, status FROM projects WHERE faculty_id = ?", (current_user.id,)).fetchall()
    return jsonify({"profile": dict(profile_data), "projects": [dict(p) for p in projects]})

@app.route('/api/faculty/project/<int:project_id>/add-milestone', methods=['POST'])
@login_required
def add_milestone(project_id):
    if current_user.role != 'faculty': return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    percentage = data.get('percentage_value')

    db = get_db()
    cursor = db.cursor()
    project = cursor.execute("SELECT id FROM projects WHERE id = ? AND faculty_id = ?", (project_id, current_user.id)).fetchone()
    if not project:
        return jsonify({"success": False, "message": "Project not found or unauthorized"}), 404

    cursor.execute(
        "INSERT INTO tasks (project_id, title, description, percentage_value, status) VALUES (?, ?, ?, ?, 'assigned')",
        (project_id, title, description, percentage)
    )
    db.commit()
    return jsonify({"success": True, "message": "Milestone added successfully."})



@app.route('/api/faculty/dashboard-stats')
@login_required
def get_faculty_dashboard_stats():
    if current_user.role != 'faculty':
        return "Unauthorized", 403
    
    db = get_db()
    cursor = db.cursor()
    
    # CORRECTED: Only select projects with 'approved' status for the dashboard overview
    projects = cursor.execute('''
        SELECT status, progress_percentage FROM projects
        WHERE faculty_id = ? AND status = 'approved'
    ''', (current_user.id,)).fetchall()
    
    total_projects = len(projects)
    completed_projects = 0
    ongoing_projects = 0

    for project in projects:
        if project['progress_percentage'] >= 100:
            completed_projects += 1
        else:
            ongoing_projects += 1
            
    return jsonify({
        "total_projects": total_projects,
        "completed_projects": completed_projects,
        "ongoing_projects": ongoing_projects
    })

@app.route('/api/faculty/project-requests')
@login_required
def get_project_requests():
    db = get_db()
    cursor = db.cursor()
    requests = cursor.execute('''
        SELECT 
            p.id, 
            p.title, 
            p.description, 
            p.department, 
            GROUP_CONCAT(s.name || ' (' || s.roll_no || ')', '; ') as team_members
        FROM projects p
        JOIN project_members pm ON p.id = pm.project_id
        JOIN students s ON pm.student_id = s.user_id
        WHERE p.faculty_id = ? AND p.status = 'pending'
        GROUP BY p.id, p.title, p.description, p.department
    ''', (current_user.id,)).fetchall()
    return jsonify([dict(r) for r in requests])

@app.route('/api/faculty/project/<int:project_id>/status', methods=['POST'])
@login_required
def update_project_status(project_id):
    data = request.get_json()
    new_status = data['status']
    remarks = data.get('remarks')
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("UPDATE projects SET status = ? WHERE id = ? AND faculty_id = ?", (new_status, project_id, current_user.id))
    
    if new_status == 'rejected' and remarks:
        cursor.execute(
            "INSERT INTO feedback (project_id, faculty_id, feedback_text) VALUES (?, ?, ?)",
            (project_id, current_user.id, remarks)
        )
    
    db.commit()
    
    if cursor.rowcount > 0: 
        return jsonify({"success": True, "message": f"Project status updated to {new_status}"})
    
    return jsonify({"success": False, "message": "Project not found or unauthorized"}), 404

@app.route('/api/faculty/project/<int:project_id>/deadline', methods=['POST'])
@login_required
def set_project_deadline(project_id):
    data = request.get_json()
    deadline = data.get('submission_date')
    if not deadline:
        return jsonify({"success": False, "message": "Submission date is required"}), 400

    db = get_db()
    cursor = db.cursor()
    project = cursor.execute("SELECT id FROM projects WHERE id = ? AND faculty_id = ?", (project_id, current_user.id)).fetchone()
    if not project:
        return jsonify({"success": False, "message": "Project not found or unauthorized"}), 404
        
    # This UPDATE command will either set the date for the first time 
    # or overwrite the existing date, effectively extending/changing it.
    cursor.execute("UPDATE projects SET submission_date = ? WHERE id = ?", (deadline, project_id))
    db.commit()
    # The message should be updated to reflect that it can be an update
    return jsonify({"success": True, "message": "Deadline set or updated successfully."})

@app.route('/api/faculty/my-projects')
@login_required
def get_faculty_my_projects():
    db = get_db()
    cursor = db.cursor()
    projects = cursor.execute("SELECT * FROM projects WHERE faculty_id = ? AND status != 'pending'", (current_user.id,)).fetchall()
    
    projects_with_tasks = []
    for project in projects:
        project_dict = dict(project)
        pending_tasks = cursor.execute("SELECT * FROM tasks WHERE project_id = ? AND status = 'pending_approval'", (project['id'],)).fetchall()
        project_dict['pending_tasks'] = [dict(t) for t in pending_tasks]
        projects_with_tasks.append(project_dict)

    return jsonify(projects_with_tasks)

@app.route('/api/faculty/task/<int:task_id>/status', methods=['POST'])
@login_required
def update_task_status(task_id):
    data = request.get_json()
    new_status = data['status']
    remarks = data.get('remarks')
    db = get_db()
    cursor = db.cursor()

    task = cursor.execute('''
        SELECT t.project_id, t.title, p.faculty_id 
        FROM tasks t JOIN projects p ON t.project_id = p.id 
        WHERE t.id = ?
    ''', (task_id,)).fetchone()

    if not task or task['faculty_id'] != current_user.id:
        return jsonify({"success": False, "message": "Task not found or unauthorized"}), 404

    # CORRECTED: Let 'rejected' be set as the status. The generic update handles this.
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    
    # Add feedback if the task was rejected and remarks were provided
    if new_status == 'rejected' and remarks:
        feedback_text = f"Feedback on task '{task['title']}': {remarks}"
        cursor.execute(
            "INSERT INTO feedback (project_id, faculty_id, feedback_text) VALUES (?, ?, ?)",
            (task['project_id'], current_user.id, feedback_text)
        )
    
    # Update project progress if the task was approved
    if new_status == 'approved':
        project_id = task['project_id']
        total_progress = cursor.execute(
            "SELECT SUM(percentage_value) FROM tasks WHERE project_id = ? AND status = 'approved'",
            (project_id,)
        ).fetchone()[0]
        
        cursor.execute("UPDATE projects SET progress_percentage = ? WHERE id = ?", (total_progress or 0, project_id))

    db.commit()
    return jsonify({"success": True, "message": f"Task status updated to {new_status}"})

# --- General API Routes ---
@app.route('/api/project/<int:project_id>')
@login_required
def get_project_details(project_id):
    db = get_db()
    cursor = db.cursor()
    
    # --- No changes to this part ---
    project_data = cursor.execute('SELECT p.*, f.name as faculty_name FROM projects p JOIN faculty f ON p.faculty_id = f.user_id WHERE p.id = ?', (project_id,)).fetchone()
    if not project_data: 
        return jsonify({"success": False, "message": "Project not found"}), 404

    # --- ENHANCED: Fetch tasks and include the name of the submitting student ---
    tasks_data = cursor.execute('''
        SELECT t.*, s.name as student_name 
        FROM tasks t 
        LEFT JOIN students s ON t.student_id = s.user_id 
        WHERE t.project_id = ? 
        ORDER BY t.id ASC
    ''', (project_id,)).fetchall()

    # --- NEW: Fetch all team members for the project ---
    members_data = cursor.execute('''
        SELECT s.name, s.roll_no 
        FROM students s 
        JOIN project_members pm ON s.user_id = pm.student_id 
        WHERE pm.project_id = ?
    ''', (project_id,)).fetchall()

    return jsonify({
        "success": True, 
        "project": dict(project_data), 
        "tasks": [dict(t) for t in tasks_data],
        "members": [dict(m) for m in members_data] # Add members to the response
    })

@app.route('/uploads/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == '__main__':
    # Local development only. Set FLASK_DEBUG=1 to enable debug mode.
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1', port=5001)
