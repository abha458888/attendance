"""
src/database.py
SQLite schema and all queries for the Registrar Attendance Management System.

Tables
------
users       -- common account fields for student / teacher / admin
students    -- student-only fields, 1:1 with users
teachers    -- teacher-only fields, 1:1 with users
attendance  -- one row per (student, course, section, date), marked by a teacher
"""
import sqlite3
from datetime import datetime, date
from pathlib import Path
from contextlib import contextmanager

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "attendance.db"

ROLE_PREFIX = {"student": "STU", "teacher": "TCH", "admin": "ADM"}


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _now():
    return datetime.utcnow().isoformat()


def _new_user_id(role, conn):
    prefix = ROLE_PREFIX[role]
    row = conn.execute("SELECT COUNT(*) AS c FROM users WHERE role = ?", (role,)).fetchone()
    return f"{prefix}{row['c'] + 1:04d}"


# ================= SCHEMA / INIT =================
def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id         TEXT PRIMARY KEY,
                username        TEXT UNIQUE NOT NULL,
                email           TEXT UNIQUE NOT NULL,
                password_hash   TEXT NOT NULL,
                full_name       TEXT NOT NULL,
                role            TEXT NOT NULL CHECK(role IN ('student','teacher','admin')),
                status          TEXT NOT NULL DEFAULT 'pending',
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked          INTEGER NOT NULL DEFAULT 0,
                last_login      TEXT,
                created_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS students (
                user_id     TEXT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                roll_number TEXT UNIQUE NOT NULL,
                father_name TEXT,
                mother_name TEXT,
                dob         TEXT,
                gender      TEXT,
                mobile      TEXT,
                address     TEXT,
                school      TEXT,
                course      TEXT,
                section     TEXT
            );

            CREATE TABLE IF NOT EXISTS teachers (
                user_id       TEXT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                phone         TEXT,
                department    TEXT,
                qualification TEXT,
                experience    TEXT,
                subjects      TEXT
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  TEXT NOT NULL REFERENCES students(user_id) ON DELETE CASCADE,
                teacher_id  TEXT NOT NULL REFERENCES teachers(user_id) ON DELETE CASCADE,
                course      TEXT NOT NULL,
                section     TEXT NOT NULL,
                att_date    TEXT NOT NULL,
                status      TEXT NOT NULL CHECK(status IN ('Present','Absent')),
                marked_at   TEXT NOT NULL,
                UNIQUE(student_id, course, section, att_date)
            );
            """
        )

        # Seed demo admin (idempotent)
        exists = conn.execute("SELECT 1 FROM users WHERE username = ?", ("admin",)).fetchone()
        if not exists:
            from src.auth import hash_password
            uid = _new_user_id("admin", conn)
            conn.execute(
                "INSERT INTO users (user_id, username, email, password_hash, full_name, "
                "role, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (uid, "admin", "admin@registrar.local", hash_password("Admin@123"),
                 "System Administrator", "admin", "active", _now()),
            )


# ================= AUTH / ACCOUNT LIFECYCLE =================
def get_user_by_login(identifier, role):
    if not identifier:
        return None
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE role = ? AND (username = ? OR email = ?)",
            (role, identifier, identifier),
        ).fetchone()
        return dict(row) if row else None


def record_failed_attempt(user_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET failed_attempts = failed_attempts + 1 WHERE user_id = ?",
            (user_id,),
        )
        row = conn.execute("SELECT failed_attempts FROM users WHERE user_id = ?", (user_id,)).fetchone()
        attempts = row["failed_attempts"]
        if attempts >= 5:
            conn.execute("UPDATE users SET locked = 1 WHERE user_id = ?", (user_id,))
        return attempts


def record_successful_login(user_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET failed_attempts = 0, last_login = ? WHERE user_id = ?",
            (_now(), user_id),
        )


def unlock_account(user_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET locked = 0, failed_attempts = 0, status = 'active' WHERE user_id = ?",
            (user_id,),
        )


def set_status(user_id, status):
    with get_conn() as conn:
        conn.execute("UPDATE users SET status = ? WHERE user_id = ?", (status, user_id))


def delete_user(user_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))


def update_password(user_id, password_hash):
    with get_conn() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (password_hash, user_id))


def is_unique(field, value):
    """field is one of: username, email, roll_number"""
    with get_conn() as conn:
        if field == "roll_number":
            row = conn.execute("SELECT 1 FROM students WHERE roll_number = ?", (value,)).fetchone()
        else:
            row = conn.execute(f"SELECT 1 FROM users WHERE {field} = ?", (value,)).fetchone()
        return row is None


# ================= REGISTRATION =================
def create_student(data, password_hash):
    with get_conn() as conn:
        uid = _new_user_id("student", conn)
        conn.execute(
            "INSERT INTO users (user_id, username, email, password_hash, full_name, role, "
            "status, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (uid, data["username"], data["email"], password_hash, data["full_name"],
             "student", "pending", _now()),
        )
        conn.execute(
            "INSERT INTO students (user_id, roll_number, father_name, mother_name, dob, gender, "
            "mobile, address, school, course, section) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (uid, data["roll_number"], data["father_name"], data["mother_name"], data["dob"],
             data["gender"], data["mobile"], data["address"], data["school"], data["course"],
             data["section"]),
        )
        return uid


def create_teacher(data, password_hash):
    with get_conn() as conn:
        uid = _new_user_id("teacher", conn)
        conn.execute(
            "INSERT INTO users (user_id, username, email, password_hash, full_name, role, "
            "status, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (uid, data["username"], data["email"], password_hash, data["full_name"],
             "teacher", "pending", _now()),
        )
        conn.execute(
            "INSERT INTO teachers (user_id, phone, department, qualification, experience, subjects) "
            "VALUES (?,?,?,?,?,?)",
            (uid, data["phone"], data["department"], data["qualification"], data["experience"],
             data["subjects"]),
        )
        return uid


def create_admin(data, password_hash):
    with get_conn() as conn:
        uid = _new_user_id("admin", conn)
        conn.execute(
            "INSERT INTO users (user_id, username, email, password_hash, full_name, role, "
            "status, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (uid, data["username"], data["email"], password_hash, data["full_name"],
             "admin", "active", _now()),
        )
        return uid


# ================= PROFILE / LOOKUPS =================
def get_full_profile(user_id, role):
    with get_conn() as conn:
        user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user:
            return None
        profile = dict(user)
        if role == "student":
            extra = conn.execute("SELECT * FROM students WHERE user_id = ?", (user_id,)).fetchone()
        elif role == "teacher":
            extra = conn.execute("SELECT * FROM teachers WHERE user_id = ?", (user_id,)).fetchone()
        else:
            extra = None
        if extra:
            profile.update(dict(extra))
        return profile


def update_profile(user_id, role, full_name, email=None, contact=None, address=None):
    with get_conn() as conn:
        conn.execute("UPDATE users SET full_name = ? WHERE user_id = ?", (full_name, user_id))
        if role == "student":
            conn.execute(
                "UPDATE students SET mobile = ?, address = COALESCE(?, address) WHERE user_id = ?",
                (contact, address, user_id),
            )
        elif role == "teacher":
            conn.execute("UPDATE teachers SET phone = ? WHERE user_id = ?", (contact, user_id))


def counts():
    with get_conn() as conn:
        pending_students = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE role='student' AND status='pending'"
        ).fetchone()["c"]
        pending_teachers = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE role='teacher' AND status='pending'"
        ).fetchone()["c"]
        active_accounts = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE status='active'"
        ).fetchone()["c"]
        admins = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE role='admin'"
        ).fetchone()["c"]
        return {
            "pending_students": pending_students,
            "pending_teachers": pending_teachers,
            "active_accounts": active_accounts,
            "admins": admins,
        }


def list_pending(role):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM users WHERE role = ? AND status = 'pending' ORDER BY created_at",
            (role,),
        ).fetchall()
        return [dict(r) for r in rows]


def list_all_non_admin():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM users WHERE role != 'admin' ORDER BY role, created_at"
        ).fetchall()
        return [dict(r) for r in rows]


# ================= ATTENDANCE =================
def get_sections():
    """Distinct (course, section) pairs that have at least one active student, with counts."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT s.course AS course, s.section AS section, COUNT(*) AS n
            FROM students s
            JOIN users u ON u.user_id = s.user_id
            WHERE u.status = 'active' AND s.course IS NOT NULL AND s.course != ''
            GROUP BY s.course, s.section
            ORDER BY s.course, s.section
            """
        ).fetchall()
        return [dict(r) for r in rows]


def get_students_by_section(course, section):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT u.user_id, u.full_name, s.roll_number
            FROM students s
            JOIN users u ON u.user_id = s.user_id
            WHERE u.status = 'active' AND s.course = ? AND s.section = ?
            ORDER BY s.roll_number
            """,
            (course, section),
        ).fetchall()
        return [dict(r) for r in rows]


def get_attendance_for_date(course, section, att_date):
    """Returns {student_id: status} for an already-marked session, if any."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT student_id, status FROM attendance WHERE course=? AND section=? AND att_date=?",
            (course, section, str(att_date)),
        ).fetchall()
        return {r["student_id"]: r["status"] for r in rows}


def mark_attendance(teacher_id, course, section, att_date, records):
    """
    records: dict of {student_id: 'Present'|'Absent'}
    Upserts one row per student for that date (overwrites if teacher re-submits).
    """
    with get_conn() as conn:
        for student_id, status in records.items():
            conn.execute(
                """
                INSERT INTO attendance (student_id, teacher_id, course, section, att_date, status, marked_at)
                VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(student_id, course, section, att_date)
                DO UPDATE SET status=excluded.status, teacher_id=excluded.teacher_id, marked_at=excluded.marked_at
                """,
                (student_id, teacher_id, course, section, str(att_date), status, _now()),
            )


def get_student_attendance(student_id):
    """Full history (most recent first) + summary counts/percentage for one student."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT att_date, course, section, status FROM attendance "
            "WHERE student_id = ? ORDER BY att_date DESC",
            (student_id,),
        ).fetchall()
        history = [dict(r) for r in rows]
        total = len(history)
        present = sum(1 for r in history if r["status"] == "Present")
        pct = round((present / total) * 100, 1) if total else 0.0
        return {
            "history": history,
            "total": total,
            "present": present,
            "absent": total - present,
            "percentage": pct,
        }


def get_attendance_overview():
    """Admin-facing summary: per (course, section) totals and overall percentage."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT course, section,
                   COUNT(*) AS total,
                   SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present
            FROM attendance
            GROUP BY course, section
            ORDER BY course, section
            """
        ).fetchall()
        overview = []
        for r in rows:
            total, present = r["total"], r["present"]
            pct = round((present / total) * 100, 1) if total else 0.0
            overview.append({
                "course": r["course"], "section": r["section"],
                "total": total, "present": present, "absent": total - present, "percentage": pct,
            })
        totals = conn.execute(
            "SELECT COUNT(*) AS total, SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present "
            "FROM attendance"
        ).fetchone()
        overall_total = totals["total"] or 0
        overall_present = totals["present"] or 0
        overall_pct = round((overall_present / overall_total) * 100, 1) if overall_total else 0.0
        return {"by_section": overview, "overall_total": overall_total,
                "overall_present": overall_present, "overall_percentage": overall_pct}
