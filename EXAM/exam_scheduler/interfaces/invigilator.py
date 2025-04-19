import streamlit as st
import sqlite3
from database.init_db import create_connection

def invigilator_interface(db_file):
    st.title("Invigilator Portal - Exam Scheduling System")
    
    # Login
    st.sidebar.header("Invigilator Login")
    invigilator_id = st.sidebar.text_input("Invigilator Code")
    passcode = st.sidebar.text_input("Passcode", type="password")
    
    if st.sidebar.button("Login"):
        if authenticate_invigilator(invigilator_id, passcode, db_file):
            st.session_state['invigilator_logged_in'] = True
            st.session_state['invigilator_id'] = invigilator_id
            st.success("Logged in successfully!")
        else:
            st.error("Invalid credentials")
    
    if st.session_state.get('invigilator_logged_in', False):
        show_invigilator_dashboard(db_file)

def authenticate_invigilator(invigilator_id, passcode, db_file):
    conn = create_connection(db_file)
    if conn is not None:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=? AND passcode=? AND role='invigilator'", 
                   (invigilator_id, passcode))
        user = cur.fetchone()
        conn.close()
        return user is not None
    return False

def show_invigilator_dashboard(db_file):
    st.header("Invigilator Dashboard")
    
    invigilator_id = st.session_state['invigilator_id']
    
    # View assigned exams
    st.subheader("Your Exam Assignments")
    
    conn = create_connection(db_file)
    assignments = conn.execute("""
        SELECT es.date, es.session, s.code, s.title, es.room_code
        FROM exam_schedule es
        JOIN subjects s ON es.subject_code = s.code
        WHERE es.invigilator_id = ?
        ORDER BY es.date, es.session
    """, (invigilator_id,)).fetchall()
    conn.close()
    
    if assignments:
        st.table(assignments)
    else:
        st.info("No exam assignments found")