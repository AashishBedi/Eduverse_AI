"""
Quick database inspector - run this to see what's in the database
"""
import sqlite3

conn = sqlite3.connect('eduverse.db')
cursor = conn.cursor()

# Check if table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='timetables'")
if not cursor.fetchone():
    print("❌ Table 'timetables' does not exist!")
    conn.close()
    exit(1)

# Get count
cursor.execute('SELECT COUNT(*) FROM timetables')
total = cursor.fetchone()[0]
print(f"Total entries: {total}")

if total == 0:
    print("❌ Database is EMPTY! Upload failed or data not committed.")
    conn.close()
    exit(1)

# Get all unique teacher UIDs
cursor.execute('SELECT DISTINCT teacher_uid FROM timetables')
uids = [row[0] for row in cursor.fetchall()]
print(f"\nAll teacher UIDs in database ({len(uids)}):")
for uid in uids:
    cursor.execute('SELECT COUNT(*) FROM timetables WHERE teacher_uid = ?', (uid,))
    count = cursor.fetchone()[0]
    print(f"  '{uid}' (len={len(uid)}, entries={count})")

# Check for 11265 specifically
print("\nSearching for '11265':")
cursor.execute("SELECT COUNT(*) FROM timetables WHERE teacher_uid = '11265'")
count = cursor.fetchone()[0]
print(f"  Exact match '11265': {count} entries")

# Check for variations
cursor.execute("SELECT COUNT(*) FROM timetables WHERE teacher_uid LIKE '%11265%'")
count = cursor.fetchone()[0]
print(f"  Contains '11265': {count} entries")

conn.close()
print("\n✅ Run this script: python quick_check.py")
