import sqlite3

conn = sqlite3.connect("students.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll TEXT NOT NULL,
    email TEXT NOT NULL,
    course TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("✅ students.db created successfully")
