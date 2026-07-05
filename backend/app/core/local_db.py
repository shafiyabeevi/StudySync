import sqlite3
import os
import json
from pathlib import Path

# Setup local storage dirs
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = os.path.join(BASE_DIR, "study_sync.db")
STORAGE_DIR = os.path.join(BASE_DIR, "storage", "documents")

os.makedirs(STORAGE_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT,
            file_type TEXT NOT NULL,
            file_size INTEGER NOT NULL DEFAULT 0,
            extracted_text TEXT,
            exam_notes TEXT,
            status TEXT NOT NULL DEFAULT 'uploading',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teach_it_back_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            document_id TEXT NOT NULL,
            topic TEXT,
            student_explanation TEXT NOT NULL,
            ai_feedback TEXT,
            score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chunk_doubt_counts (
            chunk_hash TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            doubt_count INTEGER DEFAULT 0,
            chunk_text TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    try:
        cursor.execute('ALTER TABLE chunk_doubt_counts ADD COLUMN chunk_text TEXT')
    except sqlite3.OperationalError:
        pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id_or_session_id TEXT NOT NULL,
            feature_type TEXT NOT NULL,
            reference_id TEXT,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize on import
init_db()
