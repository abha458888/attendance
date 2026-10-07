"""
app.py
Attendance Management System — Streamlit + SQLite prototype.
Run locally:   streamlit run app.py
Deploy:        see README.md (Render)
"""
import random
import string
from datetime import date

import streamlit as st

from src import database as db
from src.auth import hash_password, verify_password, is_strong_password, password_rules_html
from src.styles import get_css

st.set_page_config(page_title="Registrar — Attendance Management System",
                    page_icon="🗂️", layout="centered")

# ---------- One-time DB init ----------
if "db_ready" not in st.session_state:
    db.init_db()
    st.session_state.db_ready = True

# ---------- Session defaults ----------
defaults = {
    "view": "welcome", "user": None, "theme": "light",
    "login_role": "student", "reg_success": None,
    "reset_user_id": None, "reset_code": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.markdown(get_css(st.session_state.theme), unsafe_allow_html=True)


def go(view, **kwargs):
    st.session_state.view = view
    for k, v in kwargs.items():
        st.session_state[k] = v
    st.rerun()


def badge(status):
    return f'<span class="rg-badge {status}">{status}</span>'


# ================= TOP BAR =================
top_l, top_r = st.columns([4, 1])
with top_l:
    st.markdown(
        f'<div class="rg-eyebrow">Registrar · Attendance Management</div>',
        unsafe_allow_html=True)
with top_r:
    if st.button("◐ Theme", use_container_width=True):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()

if st.session_state.user:
    u = st.session_state.user
    st.markdown(f'<span class="rg-mono rg-muted">Signed in as {u["user_id"]} ({u["role"]})</span>',
                unsafe_allow_html=True)
    cols = st.columns([1, 1, 1, 3])
    with cols[0]:
        if st.button("Profile"):
            go("profile")
    if u["role"] == "teacher":
        with cols[1]:
            if st.button("Mark Attendance"):
                go("mark_attendance")
    with cols[2]:
        if st.button("Log out"):
            st.session_state.user = None
            go("welcome")

st.write("")


# ================= WELCOME =================
def view_welcome():
    st.markdown("""
    <div class="rg-hero">
        <div class="rg-eyebrow" style="background:rgba(255,255,255,.12); color:#8FE0D3;">Est. registrar's office · digital</div>
        <h1>Attendance, on the record.</h1>
        <p>A single ledger for students, teachers and administrators — registration, approval
        and attendance, kept properly.</p>
        <div class="rg-seal">VERIFIED<br>RECORD</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Login →", use_container_width=True):
            go("login")
    with c2:
        if st.button("Register →", use_container_width=True):
            go("register_choice")
    with c3:
        if st.button("Forgot Password →", use_container_width=True):
            go("forgot_password")
    st.caption("Demo admin — username: **admin** · password: **Admin@123**")


# ================= LOGIN =================
def view_login():
    st.markdown('<div class="rg-eyebrow">Sign in</div>', unsafe_allow_html=True)
    st.markdown("## Welcome back")
    role = st.radio("Account type", ["student", "teacher", "admin"],
                     index=["student", "teacher", "admin"].index(st.session_state.login_role),
                     horizontal=True, label_visibility="collapsed")
    st.session_state.login_role = role

    identifier = st.text_input("Username or Email")
    password = st.text_input("Password", type="password")

    if st.button("Log in", type="primary"):
        if not identifier or not password:
            st.error("Please enter both fields.")
            return
        user = db.get_user_by_login(identifier, role)
        if not user:
            st.error("No matching account found.")
            return
        if user["locked"]:
            st.error("Account locked after repeated failed attempts. Contact admin.")
            return
        if user["status"] == "suspended":
            st.error("This account has been suspended by admin.")
            return
        if user["status"] == "rejected":
            st.error("This registration was rejected. Contact admin.")
            return
        if not verify_password(password, user["password_hash"]):
            attempts = db.record_failed_attempt(user["user_id"])
            if attempts >= 5:
                st.error("Too many failed attempts. Account locked.")
            else:
                st.error(f"Incorrect password. {5 - attempts} attempt(s) remaining.")
            return
        if user["status"] == "pending":
            st.warning("Your account is pending admin approval.")
            return
        db.record_successful_login(user["user_id"])
        st.session_state.user = user
        st.success(f"Welcome, {user['full_name']}.")
        go("dashboard")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Forgot password?"):
            go("forgot_password")
    with c2:
        if st.button("Create an account"):
            go("register_choice")


# ================= REGISTER: CHOICE =================
def view_register_choice():
    st.markdown('<div class="rg-eyebrow">New account</div>', unsafe_allow_html=True)
    st.markdown("## Register")
    st.write("Choose the type of account you're creating. New accounts require admin approval before login.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Student →", use_container_width=True):
            go("register_student")
    with c2:
        if st.button("Teacher →", use_container_width=True):
            go("register_teacher")
    st.caption("Admin accounts cannot be self-registered — they're created only by an existing Admin.")
    if st.button("← Back to login"):
        go("login")


# ================= REGISTER: STUDENT =================
def view_register_student():
    st.markdown('<div class="rg-eyebrow">Register · Student</div>', unsafe_allow_html=True)
    st.markdown("## Student registration")
    st.caption("Your account will be reviewed by an admin before you can log in.")

    st.markdown("**Personal information**")
    c1, c2 = st.columns(2)
    full_name = c1.text_input("Full Name *", key="s_full_name")
    roll_number = c2.text_input("Roll Number *", key="s_roll")
    c3, c4 = st.columns(2)
    father_name = c3.text_input("Father's Name *", key="s_father")
    mother_name = c4.text_input("Mother's Name *", key="s_mother")
    c5, c6 = st.columns(2)
    dob = c5.date_input("Date of Birth *", key="s_dob", value=None, min_value=None)
    gender = c6.selectbox("Gender *", ["", "Female", "Male", "Non-binary", "Prefer not to say"], key="s_gender")

    st.markdown("**Contact**")
    c7, c8 = st.columns(2)
    email = c7.text_input("Email Address *", key="s_email")
    mobile = c8.text_input("Mobile Number *", key="s_mobile")
    address = st.text_area("Address *", key="s_address")

    st.markdown("**Academic**")
    school = st.text_input("College/School Name *", key="s_school")
    c9, c10 = st.columns(2)
    course = c9.text_input("Course *", key="s_course")
    section = c10.text_input("Section *", key="s_section")

    st.markdown("**Account**")
    username = st.text_input("Username *", key="s_username")
    c11, c12 = st.columns(2)
    pw = c11.text_input("Password *", type="password", key="s_pw")
    pw2 = c12.text_input("Confirm Password *", type="password", key="s_pw2")
    if pw:
        st.markdown(password_rules_html(pw))

    if st.button("Submit registration", type="primary"):
        required = [full_name, roll_number, father_name, mother_name, gender, email,
                    mobile, address, school, course, section, username, pw, pw2]
        if not all(required) or not dob:
            st.error("Please fill in all required fields.")
            return
        if not db.is_unique("username", username):
            st.error("Username already taken.")
            return
        if not db.is_unique("email", email):
            st.error("Email already registered.")
            return
        if not db.is_unique("roll_number", roll_number):
            st.error("Roll number already registered.")
            return
        if not is_strong_password(pw):
            st.error("Password does not meet strength requirements.")
            return
        if pw != pw2:
            st.error("Passwords do not match.")
            return
        data = dict(full_name=full_name, roll_number=roll_number, father_name=father_name,
                    mother_name=mother_name, dob=str(dob), gender=gender, email=email,
                    mobile=mobile, address=address, school=school, course=course,
                    section=section, username=username)
        uid = db.create_student(data, hash_password(pw))
        go("reg_success", reg_success={"id": uid, "role": "Student"})

    if st.button("← Back"):
        go("register_choice")


# ================= REGISTER: TEACHER =================
def view_register_teacher():
    st.markdown('<div class="rg-eyebrow">Register · Teacher</div>', unsafe_allow_html=True)
    st.markdown("## Teacher registration")
    st.caption("Your account will remain pending until an admin approves it.")

    full_name = st.text_input("Full Name *", key="t_full_name")
    c1, c2 = st.columns(2)
    email = c1.text_input("Email *", key="t_email")
    phone = c2.text_input("Phone Number *", key="t_phone")
    c3, c4 = st.columns(2)
    department = c3.text_input("Department *", key="t_dept")
    qualification = c4.text_input("Qualification *", key="t_qual")
    c5, c6 = st.columns(2)
    experience = c5.text_input("Experience (years) *", key="t_exp")
    subjects = c6.text_input("Subjects *", key="t_subjects", placeholder="e.g. Physics, Mathematics")

    st.markdown("**Account**")
    username = st.text_input("Username *", key="t_username")
    c7, c8 = st.columns(2)
    pw = c7.text_input("Password *", type="password", key="t_pw")
    pw2 = c8.text_input("Confirm Password *", type="password", key="t_pw2")
    if pw:
        st.markdown(password_rules_html(pw))

    if st.button("Submit registration", type="primary"):
        required = [full_name, email, phone, department, qualification, experience,
                    subjects, username, pw, pw2]
        if not all(required):
            st.error("Please fill in all required fields.")
            return
        if not db.is_unique("username", username):
            st.error("Username already taken.")
            return
        if not db.is_unique("email", email):
            st.error("Email already registered.")
            return
        if not is_strong_password(pw):
            st.error("Password does not meet strength requirements.")
            return
        if pw != pw2:
            st.error("Passwords do not match.")
            return
        data = dict(full_name=full_name, email=email, phone=phone, department=department,
                    qualification=qualification, experience=experience, subjects=subjects,
                    username=username)
        uid = db.create_teacher(data, hash_password(pw))
        go("reg_success", reg_success={"id": uid, "role": "Teacher"})

    if st.button("← Back"):
        go("register_choice")


# ================= REGISTER SUCCESS =================
def view_reg_success():
    info = st.session_state.reg_success or {}
    st.markdown('<div class="rg-seal" style="border-color:#2F8F82;color:#2F8F82;">RECEIVED<br>PENDING</div>',
                unsafe_allow_html=True)
    st.markdown("## Registration successful")
    st.write(f"Your {info.get('role')} account `{info.get('id')}` has been created with status "
             f"**Pending Approval**. The admin has been notified and will review it shortly. "
             f"You'll be able to log in once approved.")
    if st.button("Go to login", type="primary"):
        go("login")


# ================= FORGOT PASSWORD =================
def view_forgot_password():
    st.markdown('<div class="rg-eyebrow">Account recovery</div>', unsafe_allow_html=True)
    st.markdown("## Forgot password")

    if not st.session_state.reset_user_id:
        identifier = st.text_input("Username or Email")
        if st.button("Send reset code", type="primary"):
            user = (db.get_user_by_login(identifier, "student")
                    or db.get_user_by_login(identifier, "teacher")
                    or db.get_user_by_login(identifier, "admin"))
            if not user:
                st.error("No account matches that username or email.")
                return
            code = "".join(random.choices(string.digits, k=6))
            st.session_state.reset_user_id = user["user_id"]
            st.session_state.reset_code = code
            st.rerun()
    else:
        st.info(f"Demo mode — no email is sent. Your reset code is: **{st.session_state.reset_code}**")
        code_input = st.text_input("Enter reset code")
        c1, c2 = st.columns(2)
        new_pw = c1.text_input("New Password", type="password")
        new_pw2 = c2.text_input("Confirm New Password", type="password")
        if new_pw:
            st.markdown(password_rules_html(new_pw))
        if st.button("Reset password", type="primary"):
            if code_input != st.session_state.reset_code:
                st.error("Incorrect reset code.")
                return
            if not is_strong_password(new_pw):
                st.error("Password does not meet strength requirements.")
                return
            if new_pw != new_pw2:
                st.error("Passwords do not match.")
                return
            db.update_password(st.session_state.reset_user_id, hash_password(new_pw))
            st.success("Password reset successfully.")
            st.session_state.reset_user_id = None
            st.session_state.reset_code = None
            go("login")
    if st.button("← Back to login"):
        st.session_state.reset_user_id = None
        st.session_state.reset_code = None
        go("login")


# ================= MARK ATTENDANCE (teacher) =================
def view_mark_attendance():
    if not st.session_state.user or st.session_state.user["role"] != "teacher":
        go("login")
        return

    teacher = st.session_state.user
    st.markdown('<div class="rg-eyebrow">Teacher · Attendance</div>', unsafe_allow_html=True)
    st.markdown("## Mark attendance")

    sections = db.get_sections()
    if not sections:
        st.info("No active student sections found yet. Attendance can be marked once students "
                 "are registered and approved.")
        if st.button("← Back to dashboard"):
            go("dashboard")
        return

    options = [f"{s['course']} · Section {s['section']} ({s['n']} students)" for s in sections]
    idx = st.selectbox("Course / Section", range(len(options)), format_func=lambda i: options[i])
    chosen = sections[idx]
    course, section = chosen["course"], chosen["section"]

    att_date = st.date_input("Date", value=date.today())

    students = db.get_students_by_section(course, section)
    existing = db.get_attendance_for_date(course, section, att_date)
    if existing:
        st.caption(f"Attendance for this date was already marked — showing saved values, editable below.")

    st.write("")
    marks = {}
    for stu in students:
        prev = existing.get(stu["user_id"], "Present")
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown(
                f'<div class="rg-row"><b>{stu["full_name"]}</b> '
                f'<span class="rg-id">· Roll No. {stu["roll_number"]} · {stu["user_id"]}</span></div>',
                unsafe_allow_html=True)
        with c2:
            marks[stu["user_id"]] = st.radio(
                "Status", ["Present", "Absent"],
                index=0 if prev == "Present" else 1,
                horizontal=True, key=f"att_{stu['user_id']}_{att_date}",
                label_visibility="collapsed",
            )

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Save attendance", type="primary", use_container_width=True):
            db.mark_attendance(teacher["user_id"], course, section, att_date, marks)
            st.success(f"Attendance saved for {course} · Section {section} on {att_date}.")
    with c2:
        if st.button("← Back to dashboard", use_container_width=True):
            go("dashboard")


# ================= DASHBOARD (role-aware) =================
def view_dashboard():
    if not st.session_state.user:
        go("login")
    u = st.session_state.user
    role = u["role"]
    fresh = db.get_full_profile(u["user_id"], role)
    st.session_state.user = fresh

    if role == "admin":
        view_admin_dashboard(fresh)
        return

    st.markdown(f'<div class="rg-eyebrow">{role.title()} portal</div>', unsafe_allow_html=True)
    st.markdown(f"## Welcome, {fresh['full_name']}")
    if role == "student":
        st.caption(f"{fresh.get('course','')} · Section {fresh.get('section','')} · Roll No. {fresh.get('roll_number','')}")
    else:
        st.caption(f"{fresh.get('department','')} · {fresh.get('subjects','')}")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="rg-stat"><div class="num">{fresh["user_id"]}</div><div class="lbl">Account ID</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="rg-stat"><div class="num">{badge(fresh["status"])}</div><div class="lbl">Account status</div></div>', unsafe_allow_html=True)
    with c3:
        last = fresh["last_login"][:10] if fresh["last_login"] else "—"
        st.markdown(f'<div class="rg-stat"><div class="num">{last}</div><div class="lbl">Last login</div></div>', unsafe_allow_html=True)

    st.write("")

    if role == "teacher":
        st.markdown('<div class="rg-card">Use the <b>Mark Attendance</b> button above to record '
                     'Present/Absent for a course & section on any date.</div>', unsafe_allow_html=True)
        if st.button("Mark Attendance →"):
            go("mark_attendance")

    elif role == "student":
        summary = db.get_student_attendance(fresh["user_id"])
        if summary["total"] == 0:
            st.markdown('<div class="rg-card">Attendance records will appear here once your '
                         'teacher begins marking sessions.</div>', unsafe_allow_html=True)
        else:
            s1, s2, s3 = st.columns(3)
            with s1:
                st.markdown(f'<div class="rg-stat"><div class="num">{summary["percentage"]}%</div><div class="lbl">Attendance</div></div>', unsafe_allow_html=True)
            with s2:
                st.markdown(f'<div class="rg-stat"><div class="num">{summary["present"]}</div><div class="lbl">Present</div></div>', unsafe_allow_html=True)
            with s3:
                st.markdown(f'<div class="rg-stat"><div class="num">{summary["absent"]}</div><div class="lbl">Absent</div></div>', unsafe_allow_html=True)

            st.write("")
            st.markdown("#### Attendance history")
            for rec in summary["history"][:30]:
                st.markdown(
                    f'<div class="rg-row">{rec["att_date"]} · {rec["course"]} Section {rec["section"]} '
                    f'&nbsp;&nbsp;{badge(rec["status"])}</div>',
                    unsafe_allow_html=True)


def view_admin_dashboard(admin_user):
    st.markdown('<div class="rg-eyebrow">Admin console</div>', unsafe_allow_html=True)
    st.markdown("## Approvals & accounts")
    stats = db.counts()
    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [(c1, stats["pending_students"] or 0, "Pending students"),
                           (c2, stats["pending_teachers"] or 0, "Pending teachers"),
                           (c3, stats["active_accounts"] or 0, "Active accounts"),
                           (c4, stats["admins"] or 0, "Admins")]:
        col.markdown(f'<div class="rg-stat"><div class="num">{val}</div><div class="lbl">{lbl}</div></div>',
                      unsafe_allow_html=True)

    st.write("")
    with st.expander("＋ Create a new admin account"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full Name", key="na_name")
        email = c2.text_input("Email", key="na_email")
        c3, c4 = st.columns(2)
        username = c3.text_input("Username", key="na_username")
        pw = c4.text_input("Temporary Password", type="password", key="na_pw")
        if st.button("Create admin account"):
            if not all([name, email, username, pw]):
                st.error("All fields are required.")
            elif not db.is_unique("username", username):
                st.error("Username already taken.")
            elif not db.is_unique("email", email):
                st.error("Email already registered.")
            elif not is_strong_password(pw):
                st.error("Password does not meet strength requirements.")
            else:
                db.create_admin(dict(full_name=name, email=email, username=username), hash_password(pw))
                st.success("Admin account created.")
                st.rerun()

    def render_accounts(users, empty_msg):
        if not users:
            st.markdown(f'<div class="rg-muted">{empty_msg}</div>', unsafe_allow_html=True)
            return
        for user in users:
            with st.container():
                st.markdown(
                    f'<div class="rg-row"><b>{user["full_name"]}</b> {badge(user["status"])} '
                    f'<span class="rg-id"> · {user["user_id"]} · {user["username"]} · {user["email"]}</span></div>',
                    unsafe_allow_html=True)
                cols = st.columns(5)
                if user["status"] == "pending":
                    if cols[0].button("Approve", key=f"appr_{user['user_id']}"):
                        db.set_status(user["user_id"], "active")
                        st.rerun()
                    if cols[1].button("Reject", key=f"rej_{user['user_id']}"):
                        db.set_status(user["user_id"], "rejected")
                        st.rerun()
                if user["status"] == "active":
                    if cols[0].button("Suspend", key=f"susp_{user['user_id']}"):
                        db.set_status(user["user_id"], "suspended")
                        st.rerun()
                if user["status"] == "suspended" or user["locked"]:
                    if cols[0].button("Activate", key=f"act_{user['user_id']}"):
                        db.unlock_account(user["user_id"])
                        st.rerun()
                if cols[4].button("Delete", key=f"del_{user['user_id']}"):
                    db.delete_user(user["user_id"])
                    st.rerun()

    st.markdown("#### Pending student accounts")
    render_accounts(db.list_pending("student"), "No pending student registrations.")
    st.markdown("#### Pending teacher accounts")
    render_accounts(db.list_pending("teacher"), "No pending teacher registrations.")
    st.markdown("#### All accounts")
    render_accounts(db.list_all_non_admin(), "No accounts yet.")

    st.write("")
    st.markdown("#### Attendance overview")
    overview = db.get_attendance_overview()
    if overview["overall_total"] == 0:
        st.markdown('<div class="rg-muted">No attendance has been marked yet.</div>', unsafe_allow_html=True)
    else:
        o1, o2, o3 = st.columns(3)
        with o1:
            st.markdown(f'<div class="rg-stat"><div class="num">{overview["overall_percentage"]}%</div><div class="lbl">Overall attendance</div></div>', unsafe_allow_html=True)
        with o2:
            st.markdown(f'<div class="rg-stat"><div class="num">{overview["overall_present"]}</div><div class="lbl">Total present</div></div>', unsafe_allow_html=True)
        with o3:
            st.markdown(f'<div class="rg-stat"><div class="num">{overview["overall_total"]}</div><div class="lbl">Total records</div></div>', unsafe_allow_html=True)
        st.write("")
        for row in overview["by_section"]:
            st.markdown(
                f'<div class="rg-row">{row["course"]} · Section {row["section"]} — '
                f'{row["present"]}/{row["total"]} present ({row["percentage"]}%)</div>',
                unsafe_allow_html=True)


# ================= PROFILE =================
def view_profile():
    if not st.session_state.user:
        go("login")
    u = st.session_state.user
    fresh = db.get_full_profile(u["user_id"], u["role"])
    st.session_state.user = fresh

    st.markdown('<div class="rg-eyebrow">Account</div>', unsafe_allow_html=True)
    st.markdown("## Your profile")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"""
        <div class="rg-card">
            <b>{fresh['full_name']}</b><br>
            <span class="rg-muted">{fresh['role'].title()}</span><br><br>
            {badge(fresh['status'])}<br><br>
            <span class="rg-muted">Account ID</span><br><span class="rg-mono">{fresh['user_id']}</span><br><br>
            <span class="rg-muted">Registered</span><br><span class="rg-mono">{fresh['created_at'][:10]}</span><br><br>
            <span class="rg-muted">Last login</span><br><span class="rg-mono">{fresh['last_login'][:10] if fresh['last_login'] else '—'}</span>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("**Edit profile**")
        new_name = st.text_input("Full Name", value=fresh["full_name"], key="p_name")
        contact_val = fresh.get("mobile") or fresh.get("phone") or ""
        new_contact = st.text_input("Mobile / Phone", value=contact_val, key="p_phone")
        new_address = None
        if fresh["role"] == "student":
            new_address = st.text_area("Address", value=fresh.get("address", ""), key="p_address")
        if st.button("Save changes"):
            db.update_profile(fresh["user_id"], fresh["role"], new_name, None, new_contact, new_address)
            st.success("Profile updated.")
            st.rerun()

        st.markdown("---")
        st.markdown("**Change password**")
        cur = st.text_input("Current password", type="password", key="p_cur")
        new_pw = st.text_input("New password", type="password", key="p_new")
        new_pw2 = st.text_input("Confirm new password", type="password", key="p_new2")
        if new_pw:
            st.markdown(password_rules_html(new_pw))
        if st.button("Update password"):
            if not verify_password(cur, fresh["password_hash"]):
                st.error("Current password is incorrect.")
            elif not is_strong_password(new_pw):
                st.error("New password does not meet strength requirements.")
            elif new_pw != new_pw2:
                st.error("New passwords do not match.")
            else:
                db.update_password(fresh["user_id"], hash_password(new_pw))
                st.success("Password changed.")
                st.rerun()

    if st.button("← Back to dashboard"):
        go("dashboard")


# ================= ROUTER =================
ROUTES = {
    "welcome": view_welcome,
    "login": view_login,
    "register_choice": view_register_choice,
    "register_student": view_register_student,
    "register_teacher": view_register_teacher,
    "reg_success": view_reg_success,
    "forgot_password": view_forgot_password,
    "dashboard": view_dashboard,
    "profile": view_profile,
    "mark_attendance": view_mark_attendance,
}

ROUTES.get(st.session_state.view, view_welcome)()

st.write("")
st.caption("PROTOTYPE — passwords hashed with bcrypt, data stored in a local SQLite file. "
           "On Render's free tier the filesystem is ephemeral, so the database resets on redeploy/restart.")
