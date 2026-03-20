"""
User model
Database schema for users
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from app.db.database import Base


class User(Base):
    """
    User database model
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    # Password recovery
    security_question = Column(String, nullable=True)
    security_answer_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
