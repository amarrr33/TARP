import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = r"c:\Users\amare\Downloads\TARP\voxflow_local.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        age INTEGER NOT NULL,
        therapist_name TEXT,
        baseline_embedding BLOB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_name TEXT NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP,
        total_audio_length REAL DEFAULT 0.0,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)
    
    # 3. Predictions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        pred_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fluency_score REAL NOT NULL,
        stutter_type TEXT NOT NULL,
        confidence REAL NOT NULL,
        audio_file_path TEXT,
        synced_flag INTEGER DEFAULT 0,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
    );
    """)
    
    # 4. Reports Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        summary_notes TEXT,
        pdf_file_path TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """)
    
    conn.commit()
    conn.close()
    print("Database schema initialized successfully.")

def seed_sample_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if users already exist
    cursor.execute("SELECT COUNT(*) FROM users;")
    if cursor.fetchone()[0] > 0:
        conn.close()
        print("Database already contains seed data.")
        return

    # Add Users
    users_data = [
        ("John Doe (Patient #102)", 24, "Dr. Sarah Jenkins"),
        ("Jane Smith (Patient #105)", 31, "Dr. Robert Vance")
    ]
    cursor.executemany("INSERT INTO users (full_name, age, therapist_name) VALUES (?, ?, ?);", users_data)
    conn.commit()

    # Add Sessions & Predictions for John Doe over past 30 days
    stutter_types = ["Fluent", "Block", "Repetition", "Prolongation"]
    base_date = datetime.now() - timedelta(days=30)
    
    for day in range(30):
        current_day = base_date + timedelta(days=day)
        # Create 1-2 sessions per day
        for s_idx in range(random.randint(1, 2)):
            s_time = current_day + timedelta(hours=random.randint(9, 18), minutes=random.randint(0, 59))
            cursor.execute("INSERT INTO sessions (user_id, session_name, start_time, total_audio_length) VALUES (?, ?, ?, ?);",
                           (1, f"Practice Session Day {day+1}-{s_idx+1}", s_time.isoformat(), 120.0))
            session_id = cursor.lastrowid
            
            # Create 3-5 predictions per session
            for p_idx in range(random.randint(3, 5)):
                p_time = s_time + timedelta(seconds=p_idx * 15)
                # Gradually improving fluency score
                fluency_score = round(min(100.0, max(55.0, 65.0 + (day * 0.9) + random.uniform(-8.0, 8.0))), 1)
                stutter_type = "Fluent" if fluency_score > 78.0 else random.choice(["Block", "Repetition", "Prolongation"])
                confidence = round(random.uniform(0.85, 0.98), 2)
                
                cursor.execute("""
                    INSERT INTO predictions (session_id, timestamp, fluency_score, stutter_type, confidence, synced_flag)
                    VALUES (?, ?, ?, ?, ?, 1);
                """, (session_id, p_time.isoformat(), fluency_score, stutter_type, confidence))
                
    conn.commit()
    conn.close()
    print("Seed data for past 30 days populated successfully.")

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def fetch_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users;")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def save_prediction(self, user_id, fluency_score, stutter_type, confidence, audio_path=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get active session or create new one for today
        today_str = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT session_id FROM sessions WHERE user_id = ? AND start_time LIKE ? ORDER BY session_id DESC LIMIT 1;", (user_id, f"{today_str}%"))
        row = cursor.fetchone()
        
        if row:
            session_id = row['session_id']
        else:
            cursor.execute("INSERT INTO sessions (user_id, session_name, start_time) VALUES (?, ?, ?);",
                           (user_id, f"Live Session {today_str}", datetime.now().isoformat()))
            session_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO predictions (session_id, timestamp, fluency_score, stutter_type, confidence, audio_file_path, synced_flag)
            VALUES (?, ?, ?, ?, ?, ?, 0);
        """, (session_id, datetime.now().isoformat(), fluency_score, stutter_type, confidence, audio_path))
        
        pred_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return pred_id

    def fetch_user_predictions(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.pred_id, p.session_id, s.session_name, p.timestamp, p.fluency_score, p.stutter_type, p.confidence
            FROM predictions p
            JOIN sessions s ON p.session_id = s.session_id
            WHERE s.user_id = ?
            ORDER BY p.timestamp DESC;
        """, (user_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

if __name__ == "__main__":
    init_db()
    seed_sample_data()
