# Deploying to PythonAnywhere (free)

1. Sign up at pythonanywhere.com (free "Beginner" account). Your site will be `https://<username>.pythonanywhere.com`.
2. **Files** tab -> upload `college-project-tracker.zip` to your home folder, then open a **Bash console** and run:
       unzip college-project-tracker.zip
       cd college-project-tracker
       mkvirtualenv tracker --python=python3.10
       pip install -r requirements.txt
       python database.py          # creates project_tracker.db (run ONCE; later needs --reset and ERASES data)
3. **Web** tab -> "Add a new web app" -> **Manual configuration** -> Python 3.10.
4. On the Web tab set:
   - Source code / Working directory: `/home/<username>/college-project-tracker`
   - Virtualenv: `/home/<username>/.virtualenvs/tracker`
5. Click the **WSGI configuration file** link, delete everything in it, paste (replace <username>):
       import sys, os
       path = '/home/<username>/college-project-tracker'
       if path not in sys.path:
           sys.path.insert(0, path)
       os.environ['SECRET_KEY'] = 'put-a-long-random-string-here'
       from app import app as application
6. Back on the Web tab press the green **Reload** button, then open your link.

Demo student login created by database.py (password: `password123`):
- ENG25AD0154 (email Eng25ad0154@dsu.edu.in), plus the other roll numbers listed in database.py

Roll number format: `ENG` + 2-digit year + 2-letter branch + 4 digits (ENG25AD0154). Student email is always
`Eng25ad0154@dsu.edu.in`, generated from the roll number.

There are NO demo faculty accounts. Each faculty member creates their own account on the **Create account**
page, choosing Faculty and entering the **faculty access code**. Students then type that faculty member's
email (or name) when creating a project.

## Faculty access code
Default: `DSU-FACULTY-2026`. CHANGE IT before sharing the link, and give it only to real faculty.
Add this line to the WSGI file (step 5) with your own code:

    os.environ['FACULTY_CODE'] = 'your-own-secret-code'

Running locally instead? Set it before starting the app, e.g. (Command Prompt) `set FACULTY_CODE=your-code`.

## Upgrading an existing database
- Remove the old demo faculty without erasing anything else:  `python remove_demo_faculty.py`
- Do NOT run `python database.py --reset` unless you want to erase all data.
