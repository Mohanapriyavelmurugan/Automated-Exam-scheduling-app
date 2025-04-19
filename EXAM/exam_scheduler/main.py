import streamlit as st
from interfaces.admin import admin_interface
from interfaces.invigilator import invigilator_interface
from interfaces.student import student_interface
import os
from database.init_db import create_connection, initialize_db
def ensure_admin_user(db_file):
    """Ensure admin user exists in database"""
    conn = create_connection(db_file)
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE id='AD2279'")
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO users (id, name, passcode, role) VALUES (?, ?, ?, ?)",
                    ("AD2279", "Admin", "admin123", "admin")
                )
                conn.commit()
        finally:
            conn.close()

def main():
    st.set_page_config(page_title="Exam Scheduling System", layout="wide")
    
    # Database setup
    db_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(db_dir, exist_ok=True)
    db_file = os.path.join(db_dir, 'exam_scheduler.db')
    
    # Initialize database (force recreation if doesn't exist)
    initialize_db(db_file)
    ensure_admin_user(db_file)
    

    # Initialize session state variables
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = False
    if 'invigilator_logged_in' not in st.session_state:
        st.session_state['invigilator_logged_in'] = False
    if 'student_logged_in' not in st.session_state:
        st.session_state['student_logged_in'] = False

    # Get absolute path to database
    db_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(db_dir, exist_ok=True)
    db_file = os.path.join(db_dir, 'exam_scheduler.db')

    # Initialize database if not exists
    if not os.path.exists(db_file):
        initialize_db(db_file)

    # Role selection
    st.sidebar.title("Exam Scheduling System")
    role = st.sidebar.radio("Select Role", ["Student", "Invigilator", "Admin"])

    if role == "Admin":
        admin_interface(db_file)
    elif role == "Invigilator":
        invigilator_interface(db_file)
    elif role == "Student":
        student_interface(db_file)

if __name__ == "__main__":
    main()
