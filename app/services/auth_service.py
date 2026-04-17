"""
Auth service – JWT creation/validation, password hashing, security Q&A
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User

# ──────────────────────────────────────────────
# Hashing context
# ──────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ──────────────────────────────────────────────
# Password helpers
# ──────────────────────────────────────────────
def _truncate(plain: str) -> str:
    """Bcrypt hard-limit: passwords must not exceed 72 bytes."""
    return plain.encode("utf-8")[:72].decode("utf-8", errors="ignore")


def hash_password(plain: str) -> str:
    return pwd_context.hash(_truncate(plain))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_truncate(plain), hashed)


# ──────────────────────────────────────────────
# JWT helpers
# ──────────────────────────────────────────────
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expires = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expires})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_reset_token(email: str) -> str:
    return create_access_token(
        {"sub": email, "type": "reset"},
        expires_delta=timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES),
    )


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


# ──────────────────────────────────────────────
# User helpers
# ──────────────────────────────────────────────
def get_user_by_email(email: str, db: Session) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower()).first()


def authenticate_admin(email: str, password: str, db: Session) -> Optional[User]:
    user = get_user_by_email(email, db)
    if not user or not user.is_superuser:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_password(user: User, new_password: str, db: Session) -> None:
    user.hashed_password = hash_password(new_password)
    user.updated_at = datetime.utcnow()
    db.commit()


# ──────────────────────────────────────────────
# Default admin seeding
# ──────────────────────────────────────────────
SECURITY_QUESTIONS = [
    "What was the name of your first school?",
    "What is your mother's maiden name?",
    "What was the name of your first pet?",
    "What city were you born in?",
    "What was your childhood nickname?",
]


def get_or_create_default_admin(db: Session) -> None:
    """
    Seeds a default admin user on first startup if none exists.
    Credentials come from settings and should be changed immediately.
    """
    existing = db.query(User).filter(User.is_superuser == True).first()
    if existing:
        return  # admin already exists

    print("🔑 No admin found – seeding default admin account...")
    admin = User(
        email=settings.ADMIN_DEFAULT_EMAIL.lower(),
        full_name="Admin",
        hashed_password=hash_password(settings.ADMIN_DEFAULT_PASSWORD),
        is_active=True,
        is_superuser=True,
        # Default security question & answer (admin must update via first-login flow)
        security_question=SECURITY_QUESTIONS[0],
        security_answer_hash=hash_password("changeme"),
    )
    db.add(admin)
    db.commit()
    print(f"✅ Default admin created → email: {settings.ADMIN_DEFAULT_EMAIL}")
    print(f"   Default password: {settings.ADMIN_DEFAULT_PASSWORD}")
    print("   ⚠️  Please change the password after first login!")
