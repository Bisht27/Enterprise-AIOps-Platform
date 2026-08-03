from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
from fastapi import HTTPException, status
def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain text password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hashed value.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
):
    """
    Create JWT Access Token.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


# ==========================================================
# Secret encryption (at rest)
# ==========================================================
# Provider credentials (SMTP/WhatsApp/etc) live in .env, not the DB,
# so they're never persisted by this app in the first place. This
# utility is for the few things that ARE stored in the DB and are
# sensitive-ish -- currently ScheduledReport.recipients (see
# app/api/v1/reports/service.py) -- and is ready to reuse if a future
# "store provider credentials per-tenant in the DB" feature needs it.
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


def _fernet() -> Fernet:
    # Derive a stable 32-byte Fernet key from SECRET_KEY so no extra
    # env var is needed just for this.
    digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_value(plain_text: str) -> str:
    if not plain_text:
        return plain_text
    return _fernet().encrypt(plain_text.encode()).decode()


def decrypt_value(cipher_text: str) -> str:
    if not cipher_text:
        return cipher_text
    try:
        return _fernet().decrypt(cipher_text.encode()).decode()
    except InvalidToken:
        # Value was stored before encryption was introduced, or isn't
        # actually encrypted -- fail safe by returning it as-is rather
        # than throwing and breaking the whole request.
        return cipher_text


def mask_secret(value: str, keep: int = 4) -> str:
    """For display only -- e.g. Settings status page. Never returns
    enough of the original value to reconstruct it."""
    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return f"{'*' * (len(value) - keep)}{value[-keep:]}"