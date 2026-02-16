"""
Fee model for structured fee data storage
"""

from sqlalchemy import Column, Integer, String, Float
from app.db.database import Base


class Fee(Base):
    """
    Fee structure information
    Stores structured fee data for deterministic retrieval
    """
    __tablename__ = "fees"
    
    id = Column(Integer, primary_key=True, index=True)
    program_name = Column(String, nullable=False, index=True)
    tuition_fee = Column(Float, nullable=False)
    hostel_fee = Column(Float, nullable=True)
    exam_fee = Column(Float, nullable=True)
    other_fee = Column(Float, nullable=True)
    total_fee = Column(Float, nullable=False)
    academic_year = Column(String, nullable=False, index=True)
    department = Column(String, nullable=False, index=True)
    
    def __repr__(self):
        return f"<Fee(program={self.program_name}, total={self.total_fee})>"
