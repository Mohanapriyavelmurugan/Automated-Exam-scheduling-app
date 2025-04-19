import sqlite3
from sqlite3 import Error
import os

def create_connection(db_file):
    """Create a database connection to a SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def initialize_db(db_file):
    """Initialize the database with required tables and default admin"""
    conn = create_connection(db_file)
    if conn is not None:
        try:
            c = conn.cursor()
            
            # Create tables if they don't exist
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                passcode TEXT NOT NULL,
                role TEXT NOT NULL
            )""")
            
            c.execute("""CREATE TABLE IF NOT EXISTS departments (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL
            )""")
            
            c.execute("""CREATE TABLE IF NOT EXISTS subjects (
                code TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                semester INTEGER NOT NULL,
                department_code TEXT NOT NULL,
                FOREIGN KEY (department_code) REFERENCES departments(code)
            )""")
            
            c.execute("""CREATE TABLE IF NOT EXISTS rooms (
                code TEXT PRIMARY KEY,
                floor INTEGER NOT NULL,
                capacity INTEGER NOT NULL DEFAULT 30
            )""")
            
            c.execute("""CREATE TABLE IF NOT EXISTS exam_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                session TEXT NOT NULL,
                subject_code TEXT NOT NULL,
                invigilator_id TEXT NOT NULL,
                room_code TEXT NOT NULL,
                FOREIGN KEY (subject_code) REFERENCES subjects(code),
                FOREIGN KEY (invigilator_id) REFERENCES users(id),
                FOREIGN KEY (room_code) REFERENCES rooms(code)
            )""")
            
            # Insert default admin if not exists
            c.execute("""INSERT OR IGNORE INTO users 
                        VALUES (?, ?, ?, ?)""", 
                     ("AD2279", "Admin", "admin123", "admin"))
            
            # Insert rooms if none exist
            c.execute("SELECT COUNT(*) FROM rooms")
            if c.fetchone()[0] == 0:
                rooms = [f"TP{floor}{room:02d}" for floor in range(1, 16) for room in range(1, 9)]
                for room in rooms:
                    floor = int(room[2:4]) if room[2:4].isdigit() else int(room[2])
                    c.execute("INSERT INTO rooms VALUES (?, ?, ?)",
                              (room, floor, 30))
            
            conn.commit()
            print("Database initialized successfully")
        except Error as e:
            print(f"Error initializing database: {e}")
            conn.rollback()
        finally:
            conn.close()
