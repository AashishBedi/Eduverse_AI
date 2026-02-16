"""
Admission model for structured admission data storage
"""

from sqlalchemy import Column, Integer, String, Text
from app.db.database import Base


class Admission(Base):
    """
    Admission program information
    Stores structured admission data for deterministic retrieval
    """
    __tablename__ = "admissions"
    
    id = Column(Integer, primary_key=True, index=True)
    program_name = Column(String, nullable=False, index=True)
    eligibility = Column(Text, nullable=False)
    duration = Column(String, nullable=False)  # e.g., "4 years", "2 years"
    intake = Column(String, nullable=False)  # e.g., "60 seats", "120 seats"
    admission_process = Column(Text, nullable=False)
    contact_email = Column(String, nullable=True)
    department = Column(String, nullable=False, index=True)
    academic_year = Column(String, nullable=False, index=True)
    
    def __repr__(self):
        return f"<Admission(program={self.program_name}, department={self.department})>"
