"""
src/auth.py
Password hashing (bcrypt) and password-strength helpers.
"""
import re
import bcrypt

_SPECIAL_RE = re.compile(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]/;'`~]")


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt. Returns a str for easy DB storage."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def is_strong_password(password: str) -> bool:
    """8+ chars, at least one upper, one lower, one digit, one special char."""
    if not password or len(password) < 8:
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not _SPECIAL_RE.search(password):
        return False
    return True


def password_rules_html(password: str) -> str:
    """Live checklist of password rules, rendered as small HTML for st.markdown."""
    password = password or ""
    rules = [
        ("At least 8 characters", len(password) >= 8),
        ("One uppercase letter (A-Z)", bool(re.search(r"[A-Z]", password))),
        ("One lowercase letter (a-z)", bool(re.search(r"[a-z]", password))),
        ("One number (0-9)", bool(re.search(r"[0-9]", password))),
        ("One special character (!@#$...)", bool(_SPECIAL_RE.search(password))),
    ]
    items = ""
    for label, ok in rules:
        icon = "✅" if ok else "▫️"
        color = "#2F8F82" if ok else "#9AA0A6"
        items += (
            f'<div style="color:{color};font-size:0.82rem;line-height:1.5;">'
            f'{icon} {label}</div>'
        )
    return f'<div style="margin:2px 0 10px 2px;">{items}</div>'
