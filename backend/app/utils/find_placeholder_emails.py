"""
Diagnostic for Issue 1 (duplicate emails to admin@example.com / similar).

There's no hardcoded placeholder email anywhere in the codebase --
notify() emails every active user with email_enabled=True, using
whatever's on their `users.email` column. If a placeholder address is
receiving mail, a User row genuinely has that address, most likely
added by hand while testing, or left over from an old manual seed.

Run this from `backend/` to find it:

    python -m app.utils.find_placeholder_emails

It only reports -- it does not delete or modify anything. Deactivate
or fix the flagged account from the Users screen (or SQL) once found:

    UPDATE users SET is_active = 0 WHERE email = 'admin@example.com';
    -- or, if it should just have a real address:
    UPDATE users SET email = 'real-address@yourcompany.com' WHERE id = <id>;
"""
from app.database.session import SessionLocal
from app.models.user import User
from app.services.email_service import is_placeholder_email


def main():
    db = SessionLocal()
    try:
        suspects = [u for u in db.query(User).all() if u.email and is_placeholder_email(u.email)]

        if not suspects:
            print("No users with a placeholder/example email address were found.")
            print("If you're still seeing a stray email, check for two active users")
            print("that legitimately share the same real address, or a webhook/")
            print("integration calling notify() with a hardcoded recipient list.")
            return

        print(f"Found {len(suspects)} user(s) with a placeholder email address:\n")
        for u in suspects:
            print(f"  id={u.id}  username={u.username!r}  email={u.email!r}  is_active={u.is_active}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
