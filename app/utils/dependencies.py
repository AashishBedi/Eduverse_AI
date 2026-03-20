"""
FastAPI dependencies – reusable injection functions
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.auth_service import decode_token, get_user_by_email

security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Validates the Bearer JWT and returns the admin User object.
    Raises 401 if token is missing, expired, or not an admin.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(credentials.credentials)
    if not payload:
        raise credentials_exception
    if payload.get("type") == "reset":
        raise credentials_exception   # reset tokens can't access admin routes

    email: str = payload.get("sub")
    if not email:
        raise credentials_exception

    user = get_user_by_email(email, db)
    if not user or not user.is_superuser or not user.is_active:
        raise credentials_exception

    return user
