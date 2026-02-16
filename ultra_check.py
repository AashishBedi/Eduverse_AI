"""
Ultra-simple database check
"""
import os

output = []

# Check if DB file exists
db_path = 'eduverse.db'
output.append(f"Database file exists: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    size = os.path.getsize(db_path)
    output.append(f"Database size: {size} bytes")
    
    if size < 10000:
        output.append("⚠️ Database is very small - likely empty or just schema")
    
    # Try to connect
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        output.append(f"Tables: {tables}")
        
        # Check timetables
        if 'timetables' in tables:
            cursor.execute('SELECT COUNT(*) FROM timetables')
            count = cursor.fetchone()[0]
            output.append(f"Timetable entries: {count}")
            
            if count > 0:
                cursor.execute('SELECT DISTINCT teacher_uid FROM timetables')
                uids = [row[0] for row in cursor.fetchall()]
                output.append(f"Teacher UIDs: {uids}")
            else:
                output.append("❌ Timetables table is EMPTY!")
        else:
            output.append("❌ Timetables table does NOT exist!")
        
        conn.close()
        
    except Exception as e:
        output.append(f"Error connecting to database: {e}")
else:
    output.append("❌ Database file does NOT exist!")

# Write to file
with open('ultra_simple_output.txt', 'w') as f:
    for line in output:
        f.write(line + '\n')

print("Check ultra_simple_output.txt")
