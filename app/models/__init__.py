"""
Database models package
Exports all SQLAlchemy models
"""

from app.models.user import User
from app.models.course import Course
from app.models.document import Document
from app.models.timetable import Timetable

__all__ = ["User", "Course", "Document", "Timetable"]
