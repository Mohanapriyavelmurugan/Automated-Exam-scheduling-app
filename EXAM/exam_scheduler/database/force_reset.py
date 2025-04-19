import sqlite3
import os

def force_reset_database(db_path):
    """Completely wipe and recreate the database"""
    conn = None  # Initialize conn variable
    try:
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Close any existing connections and delete file
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Deleted existing database file: {db_path}")
        
        # Recreate database
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Create tables
        c.execute("""CREATE TABLE users (
                    id text PRIMARY KEY,
                    name text NOT NULL,
                    passcode text NOT NULL,
                    role text NOT NULL
                )""")
        
        c.execute("""CREATE TABLE departments (
                    code text PRIMARY KEY,
                    name text NOT NULL
                )""")
        
        c.execute("""CREATE TABLE subjects (
                    code text PRIMARY KEY,
                    title text NOT NULL,
                    semester integer NOT NULL,
                    department_code text NOT NULL,
                    FOREIGN KEY (department_code) REFERENCES departments(code)
                )""")
        
        c.execute("""CREATE TABLE rooms (
                    code text PRIMARY KEY,
                    floor integer NOT NULL,
                    capacity integer NOT NULL DEFAULT 30
                )""")
        
        c.execute("""CREATE TABLE exam_schedule (
                    id integer PRIMARY KEY AUTOINCREMENT,
                    date text NOT NULL,
                    session text NOT NULL,
                    subject_code text NOT NULL,
                    invigilator_id text NOT NULL,
                    room_code text NOT NULL,
                    FOREIGN KEY (subject_code) REFERENCES subjects(code),
                    FOREIGN KEY (invigilator_id) REFERENCES users(id),
                    FOREIGN KEY (room_code) REFERENCES rooms(code)
                )""")
        
        c.execute("""CREATE TABLE students (
                    ra_number text PRIMARY KEY,
                    name text NOT NULL,
                    department_code text NOT NULL,
                    semester integer NOT NULL,
                    FOREIGN KEY (department_code) REFERENCES departments(code)
                )""")
        
        # Insert default admin
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", 
                 ("AD2279", "Admin", "admin123", "admin"))
        
        # Insert rooms (15 floors x 8 rooms)
        rooms = [f"TP{floor}{room:02d}" for floor in range(1, 16) for room in range(1, 9)]
        for room in rooms:
            floor = int(room[2:4]) if room[2:4].isdigit() else int(room[2])
            c.execute("INSERT INTO rooms VALUES (?, ?, ?)", 
                     (room, floor, 30))
        
        conn.commit()
        print("Database successfully reset with clean structure")
        
    except Exception as e:
        print(f"Error during reset: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Use absolute path to avoid confusion
    db_path = os.path.abspath(os.path.join("..", "database", "exam_scheduler.db"))
    print(f"Resetting database at: {db_path}")
    force_reset_database(db_path)