"""
Direct SQL query to check database - SIMPLIFIED
"""
import sqlite3
import sys

try:
    conn = sqlite3.connect('eduverse.db')
    cursor = conn.cursor()
    
    # Simple count
    cursor.execute('SELECT COUNT(*) FROM timetables')
    total = cursor.fetchone()[0]
    
    if total == 0:
        print("DATABASE IS EMPTY - 0 entries")
        print("\nPossible causes:")
        print("1. Upload failed silently")
        print("2. Transaction not committed")
        print("3. Wrong database file")
        sys.exit(0)
    
    print(f"Total entries: {total}")
    
    # Get UIDs
    cursor.execute('SELECT DISTINCT teacher_uid FROM timetables')
    uids = cursor.fetchall()
    
    print(f"\nTeacher UIDs ({len(uids)}):")
    for (uid,) in uids:
        print(f"  '{uid}'")
    
    conn.close()
    
except sqlite3.OperationalError as e:
    print(f"ERROR: {e}")
    print("Table might not exist")
except Exception as e:
    print(f"ERROR: {e}")
