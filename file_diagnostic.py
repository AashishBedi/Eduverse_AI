"""
Database diagnostic - writes to file instead of stdout
"""
import sqlite3
import sys

output_file = 'db_diagnostic_output.txt'

with open(output_file, 'w') as f:
    try:
        f.write("=== DATABASE DIAGNOSTIC ===\n\n")
        
        conn = sqlite3.connect('eduverse.db')
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='timetables'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            f.write("❌ Table 'timetables' does NOT exist!\n")
            f.write("Run: python -c \"from app.db.database import engine, Base; from app.models.timetable import Timetable; Base.metadata.create_all(bind=engine)\"\n")
            conn.close()
            sys.exit(1)
        
        f.write("✅ Table 'timetables' exists\n\n")
        
        # Get count
        cursor.execute('SELECT COUNT(*) FROM timetables')
        total = cursor.fetchone()[0]
        f.write(f"Total entries: {total}\n\n")
        
        if total == 0:
            f.write("❌ DATABASE IS EMPTY!\n")
            f.write("\nPossible causes:\n")
            f.write("1. File upload failed\n")
            f.write("2. Transaction not committed\n")
            f.write("3. Parser returned empty list\n")
            f.write("\nCheck backend logs for errors during upload.\n")
            conn.close()
            sys.exit(0)
        
        # Get all teacher UIDs
        cursor.execute('SELECT DISTINCT teacher_uid FROM timetables ORDER BY teacher_uid')
        uids = cursor.fetchall()
        
        f.write(f"Unique teacher UIDs ({len(uids)}):\n")
        for (uid,) in uids:
            cursor.execute('SELECT COUNT(*) FROM timetables WHERE teacher_uid = ?', (uid,))
            count = cursor.fetchone()[0]
            f.write(f"  '{uid}' (length={len(uid)}, entries={count})\n")
        
        # Sample entries
        f.write("\nSample entries:\n")
        cursor.execute('SELECT teacher_uid, teacher_name, subject, day FROM timetables LIMIT 5')
        for row in cursor.fetchall():
            f.write(f"  UID='{row[0]}', Name={row[1]}, Subject={row[2]}, Day={row[3]}\n")
        
        # Test query for 11265
        f.write("\nTest queries:\n")
        for test_uid in ['11265', '23538', '18818']:
            cursor.execute('SELECT COUNT(*) FROM timetables WHERE teacher_uid = ?', (test_uid,))
            count = cursor.fetchone()[0]
            f.write(f"  teacher_uid='{test_uid}': {count} entries\n")
        
        conn.close()
        f.write("\n✅ Diagnostic complete\n")
        
    except Exception as e:
        f.write(f"\n❌ ERROR: {e}\n")
        import traceback
        f.write(traceback.format_exc())

print(f"Results written to: {output_file}")
print("Open the file to see diagnostic results.")
