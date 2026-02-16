"""
Database initialization
Creates all tables on startup
"""

from app.db.database import engine, Base
from app.models.user import User
from app.models.document import Document
from app.models.timetable import Timetable
from app.models.admission import Admission
from app.models.fee import Fee


def init_database():
    """
    Initialize database by creating all tables
    This function is called on application startup
    """
    print("🔧 Initializing database...")
    
    # Import all models to ensure they are registered with Base
    # This is important for Base.metadata.create_all() to work
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database initialized successfully!")
    print(f"   - Created tables: {', '.join(Base.metadata.tables.keys())}")


def drop_all_tables():
    """
    Drop all tables from the database
    WARNING: This will delete all data!
    Use only for development/testing
    """
    print("⚠️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped!")


if __name__ == "__main__":
    # Run this script directly to initialize the database
    init_database()
