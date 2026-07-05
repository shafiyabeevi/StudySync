import sqlite3
from app.core.local_db import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
print('tables', cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall())
print('documents', cur.execute("SELECT id, filename, status, exam_notes IS NOT NULL as has_notes FROM documents ORDER BY created_at DESC LIMIT 10").fetchall())
conn.close()
