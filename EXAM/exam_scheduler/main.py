import streamlit as st
from interfaces.admin import admin_interface
from interfaces.invigilator import invigilator_interface
from interfaces.student import student_interface
from database.init_db import reset_database
from database.init_db import initialize_db

def main():
    st.set_page_config(page_title="Exam Scheduling System", layout="wide")
    
    # Initialize session state
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = False
    if 'invigilator_logged_in' not in st.session_state:
        st.session_state['invigilator_logged_in'] = False
    if 'student_logged_in' not in st.session_state:
        st.session_state['student_logged_in'] = False
    
    # Database file
    db_file = "database/exam_scheduler.db"
    
    # Role selection
    st.sidebar.title("Exam Scheduling System")
    role = st.sidebar.radio("Select Role", ["Student", "Invigilator", "Admin"])
    
    if role == "Admin":
        admin_interface(db_file)
    elif role == "Invigilator":
        invigilator_interface(db_file)
    elif role == "Student":
        student_interface(db_file)

# Add this to your existing code
if __name__ == "__main__":
    # For testing/reset purposes
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--reset', action='store_true', help='Completely reset the database')
    parser.add_argument('--clear', action='store_true', help='Clear all data but keep tables')
    args = parser.parse_args()
    
    if args.reset:
        reset_database("database/exam_scheduler.db")
    elif args.clear:
        initialize_db("database/exam_scheduler.db")
    else:
        # Your normal application startup code
        main()