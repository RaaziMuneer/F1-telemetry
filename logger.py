import sqlite3
import time

class TelemetryLogger:
    def __init__(self, db_name="f1_telemetry.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        # We store Session UID to distinguish between different races/tracks
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS telemetry (
                session_uid UNSIGNED BIG INT,
                frame_id INTEGER,
                speed INTEGER,
                throttle REAL,
                brake REAL,
                gear INTEGER,
                rpm INTEGER,
                timestamp REAL
            )
        ''')
        self.conn.commit()

    def log_data(self, session_uid, frame_id, stats):
        self.cursor.execute('''
            INSERT INTO telemetry VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_uid,
            frame_id,
            stats['speed'],
            stats['throttle'],
            stats['brake'],
            stats['gear'],
            stats['rpm'],
            time.time()
        ))
        
    def save(self):
        self.conn.commit()

    def close(self):
        self.conn.close()