"""
Timetable model
Database schema for teacher timetables
"""

from sqlalchemy import Column, Integer, String, Time
from app.db.database import Base


class Timetable(Base):
    """
    Timetable database model
    Stores teacher schedule information
    """
    __tablename__ = "timetables"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    teacher_uid = Column(String, nullable=False, index=True)
    teacher_name = Column(String, nullable=False)
    subject = Column(String, nullable=False, index=True)
    day = Column(String, nullable=False, index=True)  # e.g., "Monday", "Tuesday"
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    classroom = Column(String, nullable=False)
    department = Column(String, nullable=False, index=True)
    
    def __repr__(self):
        return f"<Timetable(id={self.id}, teacher='{self.teacher_name}', subject='{self.subject}', day='{self.day}')>"
