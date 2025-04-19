import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to {db_file}, SQLite version: {sqlite3.version}")
        return conn
    except Error as e:
        print(e)
    return conn

def initialize_db(db_file):
    """Initialize and reset the database - clears all data but keeps table structure"""
    conn = create_connection(db_file)
    if conn is not None:
        try:
            c = conn.cursor()
            
            # Get list of all tables in the database
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in c.fetchall()]
            
            # Delete all data from all tables
            for table in tables:
                if table == 'sqlite_sequence':
                    continue  # Skip SQLite sequence table
                if table == 'users':
                    # Special case for users table - keep admin account
                    c.execute("DELETE FROM users WHERE id != 'AD2279'")
                    # Reinsert default admin user if it was deleted
                    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)", 
                             ("AD2279", "Admin", "admin123", "admin"))
                else:
                    c.execute(f"DELETE FROM {table}")
            
            # Reinsert all 120 rooms (15 floors x 8 rooms per floor)
            rooms = [f"TP{floor}{room:02d}" for floor in range(1, 16) for room in range(1, 9)]
            for room in rooms:
                floor = int(room[2:4]) if room[2:4].isdigit() else int(room[2])
                c.execute("INSERT OR IGNORE INTO rooms VALUES (?, ?, ?)", 
                         (room, floor, 30))
            
            conn.commit()
            print("All data cleared successfully. Database structure remains intact.")
        except Error as e:
            print(f"Error clearing database: {e}")
            conn.rollback()
        finally:
            conn.close()

def reset_database(db_file):
    """Completely reset the database (drop and recreate all tables)"""
    conn = create_connection(db_file)
    if conn is not None:
        try:
            c = conn.cursor()
            
            # Get list of all tables in the database
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in c.fetchall()]
            
            # Drop all tables if they exist
            for table in tables:
                if table != 'sqlite_sequence':  # Don't drop the sequence table
                    c.execute(f"DROP TABLE IF EXISTS {table}")
            
            # Recreate tables with updated schema
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                        id text PRIMARY KEY,
                        name text NOT NULL,
                        passcode text NOT NULL,
                        role text NOT NULL
                    )""")
            
            c.execute("""CREATE TABLE IF NOT EXISTS departments (
                        code text PRIMARY KEY,
                        name text NOT NULL
                    )""")
            
            c.execute("""CREATE TABLE IF NOT EXISTS subjects (
                        code text PRIMARY KEY,
                        title text NOT NULL,
                        semester integer NOT NULL,
                        department_code text NOT NULL,
                        FOREIGN KEY (department_code) REFERENCES departments(code)
                    )""")
            
            c.execute("""CREATE TABLE IF NOT EXISTS rooms (
                        code text PRIMARY KEY,
                        floor integer NOT NULL,
                        capacity integer NOT NULL DEFAULT 30
                    )""")
            
            c.execute("""CREATE TABLE IF NOT EXISTS exam_schedule (
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
            
            c.execute("""CREATE TABLE IF NOT EXISTS students (
                        ra_number text PRIMARY KEY,
                        name text NOT NULL,
                        department_code text NOT NULL,
                        semester integer NOT NULL,
                        FOREIGN KEY (department_code) REFERENCES departments(code)
                    )""")
            
            # Insert default admin user
            c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)", 
                     ("AD2279", "Admin", "admin123", "admin"))
            
            # Insert all 120 rooms (15 floors x 8 rooms per floor)
            rooms = [f"TP{floor}{room:02d}" for floor in range(1, 16) for room in range(1, 9)]
            for room in rooms:
                floor = int(room[2:4]) if room[2:4].isdigit() else int(room[2])
                c.execute("INSERT OR IGNORE INTO rooms VALUES (?, ?, ?)", 
                         (room, floor, 30))
            
            conn.commit()
            print("Database completely reset. All tables recreated.")
        except Error as e:
            print(f"Error resetting database: {e}")
            conn.rollback()
        finally:
            conn.close()

# Example usage:
if __name__ == '__main__':
    db_file = "exam_scheduler.db"
    
    # To clear all data but keep tables:
    # initialize_db(db_file)
    
    # To completely reset the database (drop and recreate tables):
    # reset_database(db_file)