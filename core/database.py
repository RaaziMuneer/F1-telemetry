import sqlite3
import time

class AsyncTelemetryLogger:
    def __init__(self, db_name="f1_telemetry.db"):
        self.db_name = db_name
        self.buffer = []
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS telemetry (
                    session_uid UNSIGNED BIG INT,
                    frame_id INTEGER,
                    speed INTEGER,
                    throttle REAL,
                    brake REAL,
                    gear INTEGER,
                    rpm INTEGER,
                    ers_energy REAL,
                    timestamp REAL
                )
            ''')

    def queue_frame(self, session_uid, frame_id, stats):
        self.buffer.append((
            session_uid,
            frame_id,
            stats.get('speed', 0),
            stats.get('throttle', 0.0),
            stats.get('brake', 0.0),
            stats.get('gear', 0),
            stats.get('rpm', 0),
            stats.get('ers_store_joules', 0.0),
            time.time()
        ))
        
        # Flush to disk when buffer hits 100 rows
        if len(self.buffer) >= 100:
            self.flush()

    def flush(self):
        if not self.buffer:
            return
        with sqlite3.connect(self.db_name) as conn:
            conn.executemany('''
                INSERT INTO telemetry VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', self.buffer)
        self.buffer.clear()