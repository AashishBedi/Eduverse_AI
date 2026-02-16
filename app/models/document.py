"""
Document model
Database schema for uploaded documents
"""

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.database import Base


class Document(Base):
    """
    Document database model
    Stores metadata about uploaded educational documents
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    department = Column(String, nullable=False, index=True)
    academic_year = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', category='{self.category}')>"
