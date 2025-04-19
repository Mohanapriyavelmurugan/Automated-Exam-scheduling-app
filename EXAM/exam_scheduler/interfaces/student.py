# interfaces/student.py
import streamlit as st
import sqlite3
from database.init_db import create_connection

def student_interface(db_file):
    st.title("Student Portal - Exam Scheduling System")
    
    # Initialize session state
    if 'student_logged_in' not in st.session_state:
        st.session_state['student_logged_in'] = False
    
    # Login form
    if not st.session_state['student_logged_in']:
        st.sidebar.header("Student Login")
        student_id = st.sidebar.text_input("RA Number", placeholder="RA2211003010001", max_chars=15).upper()
        dept_code = st.sidebar.text_input("Department Code", placeholder="ECE", max_chars=8).upper()
        semester = st.sidebar.selectbox("Semester", options=range(1, 9), index=3)
        
        if st.sidebar.button("Login"):
            if authenticate_student(student_id, dept_code, db_file):
                st.session_state['student_logged_in'] = True
                st.session_state['student_id'] = student_id
                st.session_state['dept_code'] = dept_code
                st.session_state['semester'] = semester
                st.session_state['dept_name'] = get_department_name(db_file, dept_code)
                st.rerun()
            else:
                st.error("Invalid RA Number or Department Code")
    else:
        show_student_dashboard(db_file)

def authenticate_student(student_id, dept_code, db_file):
    """Validate student credentials"""
    # Check RA format
    if len(student_id) != 15 or not student_id.startswith('RA') or not student_id[2:].isdigit():
        return False
    
    # Check department exists
    conn = create_connection(db_file)
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT code FROM departments WHERE code = ?", (dept_code,))
            return cur.fetchone() is not None
        finally:
            conn.close()
    return False

def get_department_name(db_file, dept_code):
    """Get full department name"""
    conn = create_connection(db_file)
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT name FROM departments WHERE code = ?", (dept_code,))
            result = cur.fetchone()
            return result[0] if result else dept_code
        finally:
            conn.close()
    return dept_code

def show_student_dashboard(db_file):
    st.header(f"Student Dashboard - {st.session_state['dept_name']}")
    
    # Student info
    st.write(f"RA Number: {st.session_state['student_id']}")
    st.write(f"Department: {st.session_state['dept_name']}")
    st.write(f"Semester: {st.session_state['semester']}")
    
    # View schedule button
    if st.button("View My Exam Schedule"):
        view_exam_schedule(db_file)
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

def view_exam_schedule(db_file):
    """Display filtered exam schedule for the student's department and semester"""
    conn = create_connection(db_file)
    if conn:
        try:
            query = """
                SELECT 
                    es.date, 
                    es.session,
                    d.name as department,
                    s.code as subject_code,
                    s.title as subject_title,
                    s.semester,
                    es.room_code
                FROM exam_schedule es
                JOIN subjects s ON es.subject_code = s.code
                JOIN departments d ON s.department_code = d.code
                WHERE d.code = ? AND s.semester = ?
                ORDER BY es.date, es.session
            """
            params = (st.session_state['dept_code'], st.session_state['semester'])
            exams = conn.execute(query, params).fetchall()
            
            if exams:
                st.subheader(f"Exam Schedule - Semester {st.session_state['semester']}")
                
                # Create a list of dictionaries for the table
                exam_data = []
                for idx, exam in enumerate(exams):
                    exam_data.append({
                        'S.No': idx + 1,
                        'Date': exam[0],
                        'Session': exam[1],
                        'Department': exam[2],
                        'Subject Code': exam[3],
                        'Subject Title': exam[4],
                        'Semester': exam[5],
                        'Room No.': exam[6]
                    })
                
                # Display as table only
                st.table(exam_data)
            else:
                st.info("No exams scheduled for your department and semester")
        except sqlite3.Error as e:
            st.error(f"Database error: {e}")
        finally:
            conn.close()