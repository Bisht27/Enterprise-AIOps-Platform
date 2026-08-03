from app.database.base import Base
from app.database.session import engine, SessionLocal
from app.models import User, Role, Asset

# Import all models
from app.models import Role, User

from app.core.security import hash_password

# Default login created on first run only (when the roles/users tables
# are empty) so there's always at least one account that can sign in to
# the frontend. Safe to leave in place -- it never touches the tables
# again once a role/user already exists.
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "Admin@123"
DEFAULT_ADMIN_EMAIL = "admin@aiops.local"


def init_db():
    Base.metadata.create_all(bind=engine)
    seed_default_admin()


def seed_default_admin():
    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == "Admin").first()
        if not role:
            role = Role(name="Admin", description="Full platform access")
            db.add(role)
            db.commit()
            db.refresh(role)

        existing_admin = (
            db.query(User)
            .filter(User.username == DEFAULT_ADMIN_USERNAME)
            .first()
        )
        if not existing_admin and db.query(User).count() == 0:
            admin_user = User(
                username=DEFAULT_ADMIN_USERNAME,
                email=DEFAULT_ADMIN_EMAIL,
                full_name="Administrator",
                password=hash_password(DEFAULT_ADMIN_PASSWORD),
                role_id=role.id,
            )
            db.add(admin_user)
            db.commit()
            print(
                "Seeded default admin login -> "
                f"username: {DEFAULT_ADMIN_USERNAME}  password: {DEFAULT_ADMIN_PASSWORD}"
            )
    finally:
        db.close()
