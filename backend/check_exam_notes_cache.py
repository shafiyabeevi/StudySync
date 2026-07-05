import sqlite3
from app.core.local_db import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT id, filename, exam_notes IS NOT NULL as has_notes FROM documents WHERE id = '6c0abe44-0fa8-46f9-858f-47f947e53c81'")
print(cur.fetchone())
conn.close()
