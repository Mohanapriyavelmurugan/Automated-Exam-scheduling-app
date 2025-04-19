import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from database.init_db import create_connection, initialize_db
from csp.scheduler import ExamScheduler

def authenticate_admin(admin_id, passcode, db_file):
    conn = create_connection(db_file)
    if conn is not None:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=? AND passcode=? AND role='admin'", (admin_id, passcode))
        user = cur.fetchone()
        conn.close()
        return user is not None
    return False

def manage_departments(db_file):
    st.subheader("Manage Departments")
    
    with st.expander("Add New Department"):
        with st.form("add_department"):
            dept_code = st.text_input("Department Code")
            dept_name = st.text_input("Department Name")
            
            submitted = st.form_submit_button("Add Department")
            if submitted:
                if not all([dept_code, dept_name]):
                    st.error("Both code and name are required")
                else:
                    conn = create_connection(db_file)
                    try:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO departments VALUES (?, ?)", 
                                  (dept_code, dept_name))
                        conn.commit()
                        st.success("Department added successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Department code already exists")
                    finally:
                        conn.close()
    
    st.subheader("Current Departments")
    conn = create_connection(db_file)
    departments = conn.execute("SELECT code, name FROM departments").fetchall()
    conn.close()
    
    if departments:
        df = pd.DataFrame(
            [(i+1, dept[0], dept[1]) for i, dept in enumerate(departments)],
            columns=["SNO", "Dept Code", "Dept Name"]
        )
        st.table(df)
    else:
        st.info("No departments found")

def manage_invigilators(db_file):
    st.subheader("Manage Invigilators")
    
    with st.expander("Add New Invigilator"):
        with st.form("add_invigilator"):
            inv_code = st.text_input("Invigilator Code (VS123450 format)", max_chars=8)
            inv_name = st.text_input("Invigilator Name")
            passcode = st.text_input("Passcode", type="password")
            
            submitted = st.form_submit_button("Add Invigilator")
            if submitted:
                if len(inv_code) != 7 or not inv_code.startswith('VS'):
                    st.error("Invigilator code must be in VS12345 format (7 characters)")
                else:
                    conn = create_connection(db_file)
                    try:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO users VALUES (?, ?, ?, ?)", 
                                  (inv_code, inv_name, passcode, "invigilator"))
                        conn.commit()
                        st.success("Invigilator added successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Invigilator code already exists")
                    finally:
                        conn.close()
    
    st.subheader("Current Invigilators")
    conn = create_connection(db_file)
    invigilators = conn.execute("SELECT id, name FROM users WHERE role='invigilator'").fetchall()
    conn.close()
    
    if invigilators:
        df = pd.DataFrame(
            [(i+1, inv[0], inv[1]) for i, inv in enumerate(invigilators)],
            columns=["SNO", "Invigilator Code", "Invigilator Name"]
        )
        st.table(df)
    else:
        st.info("No invigilators found")

def schedule_exams(db_file):
    st.subheader("Schedule New Exam")
    
    conn = create_connection(db_file)
    
    # Get all departments
    departments = conn.execute("SELECT code, name FROM departments").fetchall()
    
    # Check if invigilators exist
    invigilators = conn.execute("SELECT id FROM users WHERE role='invigilator'").fetchall()
    if not invigilators:
        st.error("No invigilators found. Please add invigilators first.")
        return
    
    conn.close()
    
    with st.form("exam_scheduling_form"):
        st.write("### Exam Details")
        
        col1, col2 = st.columns(2)
        with col1:
            subject_code = st.text_input("Subject Code", value="21ECE208J")
        with col2:
            subject_title = st.text_input("Subject Title", value="CONTROL SIGNALS")
        
        col1, col2 = st.columns(2)
        with col1:
            semester = st.selectbox("Semester", options=range(1, 9), index=3)
        with col2:
            if departments:
                department = st.selectbox("Department", 
                                       options=[dept[0] for dept in departments],
                                       format_func=lambda x: next((dept[1] for dept in departments if dept[0] == x), ""))
            else:
                st.error("No departments found. Please add departments first.")
                return
        
        num_students = st.number_input("Number of Students", min_value=1, max_value=1000, value=120)
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Earliest Exam Date", datetime(2025, 5, 1))
        with col2:
            end_date = st.date_input("Latest Exam Date", datetime(2025, 5, 31))
        
        submitted = st.form_submit_button("Schedule Exam")
        if submitted:
            if not all([subject_code, subject_title, department]):
                st.error("Please fill all required fields")
            elif start_date >= end_date:
                st.error("End date must be after start date")
            else:
                scheduler = ExamScheduler(db_file)
                schedule = scheduler.schedule_exam(
                    subject_code=subject_code,
                    subject_title=subject_title,
                    semester=semester,
                    department=department,
                    num_students=num_students,
                    start_date=str(start_date),
                    end_date=str(end_date)
                )
                
                if schedule:
                    if scheduler.save_schedule(schedule):
                        st.success("Exam scheduled successfully!")
                        
                        st.write("### Scheduled Exam Details")
                        
                        # Create a list of dictionaries for the table
                        exam_data = []
                        for idx, exam in enumerate(schedule):
                            exam_data.append({
                                "S.No": idx + 1,
                                "Date": exam['date'],
                                "Session": exam['session'],
                                "Subject": f"{exam['subject_code']} - {exam['subject_title']}",
                                "Department": department,
                                "Semester": semester,
                                "Invigilator": exam['invigilator_code'],
                                "Room": exam['room_code'],
                                "Students": exam['student_count']
                            })
                        
                        # Display as table
                        st.table(exam_data)
                    else:
                        st.error("Failed to save schedule to database")
                else:
                    st.error("Could not schedule exam with current constraints. Try adjusting dates or adding more invigilators.")
                    
def view_schedule(db_file):
    st.subheader("Current Exam Schedule")
    
    conn = create_connection(db_file)
    
    schedule = conn.execute("""
        SELECT es.date, es.session, s.code, s.title, d.name as department, 
               s.semester, u.name as invigilator, es.room_code
        FROM exam_schedule es
        JOIN subjects s ON es.subject_code = s.code
        JOIN departments d ON s.department_code = d.code
        JOIN users u ON es.invigilator_id = u.id
        ORDER BY es.date, es.session, es.room_code
    """).fetchall()
    
    conn.close()
    
    if schedule:
        df = pd.DataFrame(
            [(i+1, exam[0], exam[1], f"{exam[2]} - {exam[3]}", exam[4], exam[5], exam[6], exam[7]) 
             for i, exam in enumerate(schedule)],
            columns=["SNO", "Date", "Session", "Subject", "Department", "Semester", "Invigilator", "Room"]
        )
        st.table(df)
    else:
        st.info("No exams scheduled yet")

def show_admin_dashboard(db_file):
    st.header("Admin Dashboard")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Manage Departments",
        "Manage Invigilators", 
        "Schedule Exams",
        "View Schedule"
    ])
    
    with tab1:
        manage_departments(db_file)
    
    with tab2:
        manage_invigilators(db_file)
    
    with tab3:
        schedule_exams(db_file)
    
    with tab4:
        view_schedule(db_file)

def admin_interface(db_file):
    st.title("Admin Portal - Exam Scheduling System")
    
    # Login
    st.sidebar.header("Admin Login")
    admin_id = st.sidebar.text_input("Admin ID")
    passcode = st.sidebar.text_input("Passcode", type="password")
    
    if st.sidebar.button("Login"):
        if authenticate_admin(admin_id, passcode, db_file):
            st.session_state['admin_logged_in'] = True
            st.session_state['admin_id'] = admin_id
            st.success("Logged in successfully!")
        else:
            st.error("Invalid credentials")
    
    if st.session_state.get('admin_logged_in', False):
        show_admin_dashboard(db_file)

def show_admin_dashboard(db_file):
    st.header("Admin Dashboard")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Manage Departments",
        "Manage Invigilators", 
        "Schedule Exams",
        "View Schedule"
    ])
    
    with tab1:
        manage_departments(db_file)
    
    with tab2:
        manage_invigilators(db_file)
    
    with tab3:
        schedule_exams(db_file)
    
    with tab4:
        view_schedule(db_file)