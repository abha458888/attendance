# Registrar — Attendance Management System

A Registration + Login system built with **Python, Streamlit, and SQLite**, ready to deploy on **Render (Free)**.

## Features

- Student & Teacher self-registration (Admin registration is disabled for the public — only an existing Admin can create another Admin).
- Unique username / email / roll number enforcement.
- Password strength rules (8+ chars, upper, lower, number, special character), hashed with **bcrypt** (never stored in plain text).
- Accounts start as `Pending Approval`; an Admin must Approve / Reject them before the user can log in.
- Admin console: approve, reject, suspend, activate, delete accounts; create new admins.
- Account lockout after 5 failed login attempts (unlockable by an Admin).
- Forgot Password flow with a demo on-screen reset code (no real email/SMS provider is wired up).
- Profile page: edit personal info, change password, view account status / registration date / last login.
- Light / dark theme toggle.

## Project structure

```
ams/
├── app.py                  # Streamlit app & UI routing
├── requirements.txt
├── Procfile                 # Render/Heroku-style start command
├── render.yaml               # Render blueprint (Infrastructure as Code)
├── .streamlit/config.toml    # Streamlit server & theme config
├── src/
│   ├── auth.py               # bcrypt hashing + password strength rules
│   ├── database.py           # SQLite schema & all queries
│   └── styles.py              # Custom CSS theme
└── data/                     # SQLite database file lives here at runtime
```

## Run locally

```bash
cd ams
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

**Demo admin login:** username `admin`, password `Admin@123`
(seeded automatically the first time the app runs and creates `data/attendance.db`).

## Deploy to Render (Free)

1. Push this folder to a GitHub repository.
2. In Render, click **New → Blueprint** and point it at the repo — it will read `render.yaml` automatically.
   - Or click **New → Web Service**, connect the repo, and set:
     - **Build command:** `pip install -r requirements.txt`
     - **Start command:** `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
3. Deploy. Render will give you a public URL.

### Important note on SQLite + Render's free tier
Render's free web services use an **ephemeral filesystem** — anything written to disk (including `data/attendance.db`) is wiped on every redeploy or when the service spins down and back up. That's fine for demoing this project, but for real, persistent data you'd want either:
- a Render **paid** plan with a persistent disk attached, or
- swapping SQLite for a managed database (e.g. Render's free PostgreSQL) later.

## Security notes (read before using with real data)

- Passwords are hashed with bcrypt — good practice, but this app has no HTTPS/session-hardening layer of its own beyond what Render/Streamlit provide.
- The Forgot Password flow shows the reset code on-screen instead of emailing it, since no email provider is configured. Wire up an email/SMS API (e.g. SendGrid, Twilio) before using this in production.
- SQL queries are parameterized throughout to prevent SQL injection.
- This is a learning/demo-grade project, not an audited production system.
