import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path

from configs.config import DB_CONFIG

def get_db_connection():
    db_path = DB_CONFIG['path']
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        started_at TIMESTAMP,
        ended_at TIMESTAMP,
        duration REAL,
        audio_path TEXT,
        model_version TEXT,
        status TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # 3. session_windows table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS session_windows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        start_time REAL NOT NULL,
        end_time REAL NOT NULL,
        predicted_class TEXT NOT NULL,
        fluent_probability REAL NOT NULL,
        repetition_probability REAL NOT NULL,
        prolongation_probability REAL NOT NULL,
        block_probability REAL NOT NULL,
        confidence REAL NOT NULL,
        FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );
    """)

    # 4. session_events table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS session_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        start_time REAL NOT NULL,
        end_time REAL NOT NULL,
        confidence REAL NOT NULL,
        supporting_window_count INTEGER NOT NULL,
        FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );
    """)

    # 5. session_summary table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS session_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE NOT NULL,
        valid_windows INTEGER NOT NULL,
        fluent_windows INTEGER NOT NULL,
        repetition_events INTEGER NOT NULL,
        prolongation_events INTEGER NOT NULL,
        block_events INTEGER NOT NULL,
        fluency_ratio REAL NOT NULL,
        FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_windows_session_id ON session_windows(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_session_id ON session_events(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_summary_session_id ON session_summary(session_id);")

    # Ensure a default user exists
    cursor.execute("INSERT OR IGNORE INTO users (id, name) VALUES ('user_default', 'VoxFlow Primary User');")

    conn.commit()
    conn.close()

def save_session_record(session_id, user_id, started_at, ended_at, duration, audio_path, model_version, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO sessions (id, user_id, started_at, ended_at, duration, audio_path, model_version, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_id, user_id, started_at, ended_at, duration, audio_path, model_version, status))
    conn.commit()
    conn.close()

def save_session_analysis(session_id, windows, events, summary):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear prior analysis if re-analyzing
    cursor.execute("DELETE FROM session_windows WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM session_events WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM session_summary WHERE session_id = ?", (session_id,))

    # Insert windows
    for w in windows:
        cursor.execute("""
            INSERT INTO session_windows (session_id, start_time, end_time, predicted_class, 
                fluent_probability, repetition_probability, prolongation_probability, block_probability, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, w['start_time'], w['end_time'], w['predicted_class'],
              w['fluent_probability'], w['repetition_probability'], w['prolongation_probability'],
              w['block_probability'], w['confidence']))

    # Insert events
    for e in events:
        cursor.execute("""
            INSERT INTO session_events (session_id, event_type, start_time, end_time, confidence, supporting_window_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, e['event_type'], e['start_time'], e['end_time'], e['confidence'], e['supporting_window_count']))

    # Insert summary
    cursor.execute("""
        INSERT INTO session_summary (session_id, valid_windows, fluent_windows, repetition_events, 
            prolongation_events, block_events, fluency_ratio)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, summary['valid_windows'], summary['fluent_windows'], summary['repetition_events'],
          summary['prolongation_events'], summary['block_events'], summary['fluency_ratio']))

    # Update session status
    cursor.execute("UPDATE sessions SET status = 'ANALYZED' WHERE id = ?", (session_id,))

    conn.commit()
    conn.close()

def get_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    s_row = cursor.fetchone()
    if not s_row:
        conn.close()
        return None

    session_data = dict(s_row)

    # Get summary
    cursor.execute("SELECT * FROM session_summary WHERE session_id = ?", (session_id,))
    sum_row = cursor.fetchone()
    session_data['summary'] = dict(sum_row) if sum_row else None

    # Get events
    cursor.execute("SELECT * FROM session_events WHERE session_id = ? ORDER BY start_time ASC", (session_id,))
    session_data['events'] = [dict(r) for r in cursor.fetchall()]

    # Get windows
    cursor.execute("SELECT * FROM session_windows WHERE session_id = ? ORDER BY start_time ASC", (session_id,))
    session_data['windows'] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return session_data

def get_latest_session():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM sessions WHERE status = 'ANALYZED' ORDER BY started_at DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return get_session(row['id'])
    return None

def get_all_sessions(user_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT * FROM sessions WHERE user_id = ? ORDER BY started_at DESC", (user_id,))
    else:
        cursor.execute("SELECT * FROM sessions ORDER BY started_at DESC")
    sessions = [dict(r) for r in cursor.fetchall()]

    for s in sessions:
        cursor.execute("SELECT * FROM session_summary WHERE session_id = ?", (s['id'],))
        sum_row = cursor.fetchone()
        s['summary'] = dict(sum_row) if sum_row else None

    conn.close()
    return sessions
