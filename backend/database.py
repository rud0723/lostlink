import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "lostlink.db")


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT NOT NULL,
            reporter_name TEXT,
            reporter_role TEXT NOT NULL,
            category TEXT,
            color TEXT,
            brand TEXT,
            description TEXT,
            location TEXT,
            latitude REAL,
            longitude REAL,
            date_time TEXT,
            photo_path TEXT
        )
    """)

    # Add latitude/longitude to an existing database
    # if the columns are not already present.
    c.execute("PRAGMA table_info(reports)")
    columns = [row[1] for row in c.fetchall()]

    if "latitude" not in columns:
        c.execute(
            "ALTER TABLE reports ADD COLUMN latitude REAL"
        )

    if "longitude" not in columns:
        c.execute(
            "ALTER TABLE reports ADD COLUMN longitude REAL"
        )

    conn.commit()
    conn.close()