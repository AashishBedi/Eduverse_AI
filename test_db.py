"""
Test script to verify database setup
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.init_db import init_database
from app.db.database import engine, SessionLocal
from app.models import Document, Timetable
from datetime import datetime, time

def test_database():
    """Test database initialization and basic operations"""
    
    print("=" * 60)
    print("Testing EduVerse AI Database Setup")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_database()
    
    # Create a session
    print("\n2. Creating database session...")
    db = SessionLocal()
    
    try:
        # Test Document model
        print("\n3. Testing Document model...")
        test_doc = Document(
            filename="test_syllabus.pdf",
            category="Syllabus",
            department="Computer Science",
            academic_year="2023-2024"
        )
        db.add(test_doc)
        db.commit()
        db.refresh(test_doc)
        print(f"   ✅ Created document: {test_doc}")
        
        # Test Timetable model
        print("\n4. Testing Timetable model...")
        test_timetable = Timetable(
            teacher_uid="T001",
            teacher_name="Dr. John Smith",
            subject="Database Systems",
            day="Monday",
            start_time=time(9, 0),
            end_time=time(10, 30),
            classroom="Room 101",
            department="Computer Science"
        )
        db.add(test_timetable)
        db.commit()
        db.refresh(test_timetable)
        print(f"   ✅ Created timetable entry: {test_timetable}")
        
        # Query data
        print("\n5. Querying data...")
        doc_count = db.query(Document).count()
        timetable_count = db.query(Timetable).count()
        print(f"   📊 Documents in database: {doc_count}")
        print(f"   📊 Timetable entries in database: {timetable_count}")
        
        # Clean up test data
        print("\n6. Cleaning up test data...")
        db.delete(test_doc)
        db.delete(test_timetable)
        db.commit()
        print("   ✅ Test data cleaned up")
        
        print("\n" + "=" * 60)
        print("✅ All database tests passed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_database()
