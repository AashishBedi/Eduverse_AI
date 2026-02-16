import sqlite3
import sys

# Connect to database
conn = sqlite3.connect('eduverse.db')
cursor = conn.cursor()

# Check total entries
cursor.execute('SELECT COUNT(*) FROM timetables')
total = cursor.fetchone()[0]
print(f"Total timetable entries: {total}")

if total == 0:
    print("\n❌ DATABASE IS EMPTY!")
    print("You need to upload a timetable file through the admin panel.")
    sys.exit(0)

# Get distinct teacher UIDs
cursor.execute('SELECT DISTINCT teacher_uid FROM timetables')
uids = [row[0] for row in cursor.fetchall()]
print(f"\nUnique teacher UIDs ({len(uids)}):")
for uid in uids:
    print(f"  '{uid}' (length: {len(uid)})")

# Sample entries
print("\nSample entries:")
cursor.execute('SELECT teacher_uid, teacher_name, subject, day FROM timetables LIMIT 5')
for row in cursor.fetchall():
    print(f"  teacher_uid='{row[0]}' (len={len(row[0])}), name={row[1]}, subject={row[2]}, day={row[3]}")

# Try to find 11265
print("\nSearching for teacher_uid='11265':")
cursor.execute("SELECT COUNT(*) FROM timetables WHERE teacher_uid = '11265'")
count = cursor.fetchone()[0]
print(f"  Found {count} entries")

# Try variations
variations = ['11265', ' 11265', '11265 ', ' 11265 ', '23538', '18818']
print("\nTrying variations:")
for var in variations:
    cursor.execute("SELECT COUNT(*) FROM timetables WHERE teacher_uid = ?", (var,))
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"  ✅ '{var}' (len={len(var)}): {count} entries")

conn.close()
