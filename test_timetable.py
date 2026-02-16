"""
Test script for timetable service
Tests deterministic timetable retrieval
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.timetable_service import timetable_service
from app.db.database import SessionLocal
from app.models.timetable import Timetable
from datetime import time


def setup_test_data(db):
    """Create sample timetable data"""
    
    # Clear existing test data
    db.query(Timetable).filter(Timetable.teacher_uid.like("T%")).delete()
    db.commit()
    
    # Create sample entries
    sample_entries = [
        Timetable(
            teacher_uid="T001",
            teacher_name="Dr. John Smith",
            subject="Database Systems",
            day="Monday",
            start_time=time(9, 0),
            end_time=time(10, 30),
            classroom="Room 101",
            department="Computer Science"
        ),
        Timetable(
            teacher_uid="T001",
            teacher_name="Dr. John Smith",
            subject="Web Development",
            day="Monday",
            start_time=time(11, 0),
            end_time=time(12, 30),
            classroom="Room 102",
            department="Computer Science"
        ),
        Timetable(
            teacher_uid="T001",
            teacher_name="Dr. John Smith",
            subject="Database Systems",
            day="Wednesday",
            start_time=time(14, 0),
            end_time=time(15, 30),
            classroom="Room 101",
            department="Computer Science"
        ),
        Timetable(
            teacher_uid="T002",
            teacher_name="Prof. Jane Doe",
            subject="Machine Learning",
            day="Monday",
            start_time=time(9, 0),
            end_time=time(10, 30),
            classroom="Room 201",
            department="Computer Science"
        ),
        Timetable(
            teacher_uid="T002",
            teacher_name="Prof. Jane Doe",
            subject="Deep Learning",
            day="Tuesday",
            start_time=time(14, 0),
            end_time=time(16, 0),
            classroom="Lab 301",
            department="Computer Science"
        ),
    ]
    
    for entry in sample_entries:
        db.add(entry)
    db.commit()
    
    print(f"✅ Created {len(sample_entries)} sample timetable entries")


def test_timetable_service():
    """Test the timetable service"""
    
    print("=" * 80)
    print("Testing EduVerse AI Timetable Service")
    print("=" * 80)
    
    # Setup database
    db = SessionLocal()
    
    try:
        # Setup test data
        print("\n📚 Step 1: Setting up test data...")
        setup_test_data(db)
        
        # Test queries
        test_queries = [
            "Show me timetable for T001",
            "What classes does T001 have on Monday?",
            "Show Monday schedule",
            "T002 Tuesday",
            "What is the schedule for Wednesday?",
            "Random query without teacher or day"
        ]
        
        print("\n🔍 Step 2: Testing timetable queries...")
        print("=" * 80)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n[Query {i}] {query}")
            print("-" * 80)
            
            # Query timetable
            result = timetable_service.query_timetable(query, db)
            
            print(f"\n📊 Query Type: {result['query_type']}")
            print(f"   Teacher UID: {result['teacher_uid']}")
            print(f"   Day: {result['day']}")
            print(f"   Entries Found: {result['count']}")
            
            # Format as text
            formatted = timetable_service.format_timetable_text(result)
            print(f"\n📝 Formatted Output:")
            print(formatted)
            
            print("\n" + "=" * 80)
        
        print("\n✅ All timetable tests completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_timetable_service()
