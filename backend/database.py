import sqlite3
import os


# ============================================================
# LOSTLINK DATABASE CONFIGURATION
# ============================================================

# Project root:
# C:\LostLink

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# Data folder:
# C:\LostLink\data

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)


# Database:
# C:\LostLink\data\lostlink.db

DB_PATH = os.path.join(
    DATA_DIR,
    "lostlink.db"
)


# Make sure data folder exists

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    conn = sqlite3.connect(DB_PATH)

    c = conn.cursor()


    # --------------------------------------------------------
    # ITEMS TABLE
    # --------------------------------------------------------

    c.execute("""
        CREATE TABLE IF NOT EXISTS items (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            code TEXT UNIQUE NOT NULL,

            name TEXT NOT NULL,

            category TEXT,

            color TEXT,

            brand TEXT,

            private_detail TEXT,

            status TEXT DEFAULT 'REGISTERED'

        )
    """)


    # --------------------------------------------------------
    # REPORTS TABLE
    # --------------------------------------------------------

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

            location TEXT NOT NULL,

            latitude REAL,

            longitude REAL,

            date_time TEXT NOT NULL,

            photo_path TEXT

        )
    """)


    # --------------------------------------------------------
    # Add latitude / longitude if an older database exists
    # --------------------------------------------------------

    try:

        c.execute(
            "ALTER TABLE reports ADD COLUMN latitude REAL"
        )

    except sqlite3.OperationalError:
        pass


    try:

        c.execute(
            "ALTER TABLE reports ADD COLUMN longitude REAL"
        )

    except sqlite3.OperationalError:
        pass


    conn.commit()

    conn.close()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    init_db()

    print("LostLink database initialized successfully.")

    print(
        "Database location:",
        DB_PATH
    )