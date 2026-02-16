import sqlite3
import os

db_path = 'eduverse.db'

print(f"Checking database: {db_path}")
print(f"Database exists: {os.path.exists(db_path)}")
print(f"Database size: {os.path.getsize(db_path) if os.path.exists(db_path) else 0} bytes")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nTables in database: {[t[0] for t in tables]}")
    
    # Check timetables table
    if ('timetables',) in tables:
        cursor.execute('SELECT COUNT(*) FROM timetables')
        total = cursor.fetchone()[0]
        print(f"\n✅ Timetables table exists")
        print(f"Total entries: {total}")
        
        if total > 0:
            # Get distinct teacher UIDs
            cursor.execute('SELECT DISTINCT teacher_uid FROM timetables')
            uids = [row[0] for row in cursor.fetchall()]
            print(f"\nUnique teacher UIDs ({len(uids)}):")
            for uid in uids[:10]:  # Show first 10
                print(f"  '{uid}' (length: {len(uid)})")
            
            # Sample entries
            print("\nSample entries:")
            cursor.execute('SELECT teacher_uid, teacher_name, subject FROM timetables LIMIT 3')
            for row in cursor.fetchall():
                print(f"  UID: '{row[0]}', Name: {row[1]}, Subject: {row[2]}")
        else:
            print("\n❌ Timetables table is EMPTY!")
            print("You need to upload a timetable file.")
    else:
        print("\n❌ Timetables table does NOT exist!")
        print("Database schema not initialized.")
    
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
