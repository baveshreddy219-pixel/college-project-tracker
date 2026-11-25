"""
Removes the four built-in demo faculty accounts (DSMITH, DJOHNSON, DWILLIAMS, DAVIS)
from an EXISTING project_tracker.db, without touching students or faculty you created.

Run once:   python remove_demo_faculty.py

It also deletes projects that were sent to those demo accounts (plus their milestones,
feedback and team links), because nobody can log in as them any more.
"""
import os
import sqlite3
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'project_tracker.db')
DEMO_USERNAMES = ('DSMITH', 'DJOHNSON', 'DWILLIAMS', 'DAVIS')
DEMO_EMAILS = tuple(f'dr.{n}@{d}' for n in ('smith', 'johnson', 'williams', 'davis')
                    for d in ('dsu.edu.in', 'college.edu'))


def main():
    if not os.path.exists(DB_PATH):
        print("project_tracker.db not found. Run this from the project folder.")
        return 1
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Safety: only accounts with a demo username AND a demo email are removed.
    marks = ','.join('?' * len(DEMO_USERNAMES))
    emarks = ','.join('?' * len(DEMO_EMAILS))
    demo = cur.execute(
        f"SELECT u.id, u.username, f.name FROM users u JOIN faculty f ON f.user_id = u.id "
        f"WHERE u.role = 'faculty' AND u.username IN ({marks}) AND lower(f.email) IN ({emarks})",
        DEMO_USERNAMES + DEMO_EMAILS).fetchall()

    if not demo:
        print("No demo faculty accounts found. Nothing to do.")
        return 0

    ids = [d[0] for d in demo]
    idmarks = ','.join('?' * len(ids))
    projects = cur.execute(f"SELECT id, title FROM projects WHERE faculty_id IN ({idmarks})", ids).fetchall()

    print("This will delete these demo faculty accounts:")
    for _, username, name in demo:
        print(f"  - {username}  ({name})")
    print(f"and {len(projects)} project(s) sent to them:")
    for _, title in projects:
        print(f"  - {title}")
    if input("\nType YES to continue: ").strip() != 'YES':
        print("Cancelled. Nothing was changed.")
        return 0

    pids = [p[0] for p in projects]
    if pids:
        pm = ','.join('?' * len(pids))
        cur.execute(f"DELETE FROM tasks WHERE project_id IN ({pm})", pids)
        cur.execute(f"DELETE FROM feedback WHERE project_id IN ({pm})", pids)
        cur.execute(f"DELETE FROM project_members WHERE project_id IN ({pm})", pids)
        cur.execute(f"DELETE FROM projects WHERE id IN ({pm})", pids)
    cur.execute(f"DELETE FROM feedback WHERE faculty_id IN ({idmarks})", ids)
    cur.execute(f"DELETE FROM faculty WHERE user_id IN ({idmarks})", ids)
    cur.execute(f"DELETE FROM users WHERE id IN ({idmarks})", ids)
    conn.commit()
    conn.close()
    print("Done. Demo faculty removed.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
