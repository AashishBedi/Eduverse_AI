"""
Debug script to check timetable database contents
"""

from app.db.database import SessionLocal
from app.models.timetable import Timetable

def check_database():
    db = SessionLocal()
    
    try:
        # Check total entries
        total = db.query(Timetable).count()
        print(f"Total timetable entries: {total}")
        
        if total == 0:
            print("❌ Database is EMPTY! No timetable data has been ingested.")
            return
        
        # Get unique teacher UIDs
        uids = db.query(Timetable.teacher_uid).distinct().all()
        print(f"\nUnique teacher UIDs ({len(uids)}):")
        for uid in uids:
            print(f"  '{uid[0]}' (length: {len(uid[0])})")
        
        # Sample entries
        print("\nSample entries:")
        results = db.query(Timetable).limit(5).all()
        for r in results:
            print(f"  teacher_uid='{r.teacher_uid}' (len={len(r.teacher_uid)})")
            print(f"    name={r.teacher_name}, subject={r.subject}, day={r.day}")
        
        # Try to query for specific teacher
        test_uid = "11265"
        print(f"\nTesting query for teacher_uid='{test_uid}':")
        results = db.query(Timetable).filter(Timetable.teacher_uid == test_uid).all()
        print(f"  Found {len(results)} entries")
        
        # Try with different variations
        for variation in ["11265", " 11265", "11265 ", " 11265 "]:
            results = db.query(Timetable).filter(Timetable.teacher_uid == variation).all()
            if len(results) > 0:
                print(f"  ✅ Found {len(results)} entries with variation: '{variation}'")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_database()
