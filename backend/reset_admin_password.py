"""
One-off script: reset the 'admin' user's password.

Run from the backend/ folder (same place you run uvicorn from), with
your venv active so it can import the app package and read .env:

    python reset_admin_password.py

Change NEW_PASSWORD below first if you want something other than the
default.
"""

from app.database.session import SessionLocal
from app.core.security import hash_password
from app.models.user import User

USERNAME = "admin"
NEW_PASSWORD = "Admin@123"

db = SessionLocal()
try:
    user = db.query(User).filter(User.username == USERNAME).first()
    if not user:
        print(f"No user with username '{USERNAME}' found.")
    else:
        user.password = hash_password(NEW_PASSWORD)
        user.failed_login_count = 0
        db.commit()
        print(f"Password for '{USERNAME}' has been reset to: {NEW_PASSWORD}")
finally:
    db.close()