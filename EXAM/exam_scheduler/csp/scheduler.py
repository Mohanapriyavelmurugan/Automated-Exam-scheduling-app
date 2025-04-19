from constraint import Problem
from datetime import datetime, timedelta
import sqlite3
from database.init_db import create_connection
from collections import defaultdict
import random
import pandas as pd
import streamlit as st


class ExamScheduler:
    def __init__(self, db_file):
        self.db_file = db_file
        self.problem = Problem()
        self.max_students_per_room = 30
        self._load_resources()
        self.sessions = ['FN', 'AN']  # Both sessions available

    def _load_resources(self):
        """Load all necessary resources from database"""
        conn = create_connection(self.db_file)
        if conn:
            try:
                # Load rooms
                cur = conn.cursor()
                cur.execute("SELECT code FROM rooms")
                self.all_rooms = [row[0] for row in cur.fetchall()]
                
                # Load invigilators
                cur.execute("SELECT id, name FROM users WHERE role='invigilator'")
                self.all_invigilators = [{'code': row[0], 'name': row[1]} for row in cur.fetchall()]
                
                # Load departments
                cur.execute("SELECT code FROM departments")
                self.departments = [row[0] for row in cur.fetchall()]
                
            except sqlite3.Error as e:
                print(f"Error loading resources: {e}")
                self.all_rooms = []
                self.all_invigilators = []
                self.departments = []
            finally:
                conn.close()
        else:
            self.all_rooms = []
            self.all_invigilators = []
            self.departments = []

    def _get_available_invigilators_for_exam(self, rooms_needed, date, session):
        """Get available invigilators for the exam based on existing schedule"""
        conn = create_connection(self.db_file)
        if not conn:
            return []
            
        try:
            cur = conn.cursor()
            # Get all invigilators who are not already assigned in conflicting exams
            cur.execute("""
                SELECT u.id FROM users u
                WHERE u.role='invigilator' 
                AND u.id NOT IN (
                    SELECT es.invigilator_id FROM exam_schedule es
                    WHERE es.date = ? AND es.session = ?
                )
                AND u.id NOT IN (
                    SELECT es.invigilator_id FROM exam_schedule es
                    WHERE es.date = ? AND es.session != ?
                )
                LIMIT ?
            """, (date, session, date, session, rooms_needed))
            
            available = [row[0] for row in cur.fetchall()]
            
            # If we don't have enough, try to find ones with minimal conflicts
            if len(available) < rooms_needed:
                cur.execute("""
                    SELECT u.id, COUNT(e.id) as assignment_count
                    FROM users u
                    LEFT JOIN exam_schedule e ON u.id = e.invigilator_id
                    WHERE u.role='invigilator'
                    GROUP BY u.id
                    ORDER BY assignment_count ASC
                    LIMIT ?
                """, (rooms_needed,))
                available = [row[0] for row in cur.fetchall()]
                
            return available if len(available) >= rooms_needed else []
            
        except sqlite3.Error as e:
            print(f"Error getting available invigilators: {e}")
            return []
        finally:
            conn.close()

    def _get_existing_schedule(self):
        """Get existing exam schedule from database"""
        conn = create_connection(self.db_file)
        if not conn:
            return []
            
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT es.date, es.session, es.room_code, es.invigilator_id, 
                       s.semester, s.department_code as department
                FROM exam_schedule es
                JOIN subjects s ON es.subject_code = s.code
            """)
            
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
            
        except sqlite3.Error as e:
            print(f"Error loading existing schedule: {e}")
            return []
        finally:
            conn.close()

    def _get_available_rooms_for_exam(self, rooms_needed, date, session):
        """Get rooms not already booked for the given date and session"""
        conn = create_connection(self.db_file)
        if not conn:
            return []
            
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT room_code FROM exam_schedule
                WHERE date = ? AND session = ?
            """, (date, session))
            
            booked_rooms = {row[0] for row in cur.fetchall()}
            available_rooms = [room for room in self.all_rooms if room not in booked_rooms]
            
            return available_rooms[:rooms_needed] if len(available_rooms) >= rooms_needed else []
            
        except sqlite3.Error as e:
            print(f"Error getting available rooms: {e}")
            return []
        finally:
            conn.close()

    def _is_department_available(self, department, date):
        """Check if department has no exam scheduled on given date"""
        conn = create_connection(self.db_file)
        if not conn:
            return False
            
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM exam_schedule es
                JOIN subjects s ON es.subject_code = s.code
                WHERE s.department_code = ? AND es.date = ?
            """, (department, date))
            
            count = cur.fetchone()[0]
            return count == 0
            
        except sqlite3.Error as e:
            print(f"Error checking department availability: {e}")
            return False
        finally:
            conn.close()

    def schedule_exam(self, subject_code, subject_title, semester, department, num_students, start_date, end_date):
        """Main scheduling method with all constraints"""
        if not self.all_rooms or not self.all_invigilators:
            return None
            
        rooms_needed = (num_students - 1) // self.max_students_per_room + 1
        if rooms_needed > len(self.all_rooms):
            return None
        
        # Generate date range (only weekdays)
        dates = []
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        while current <= end:
            if current.weekday() < 5:  # Monday-Friday
                dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        
        if not dates:
            return None
            
        # Try to find a valid schedule by checking dates in order
        for date in dates:
            for session in self.sessions:
                # Check if department is available on this date
                if not self._is_department_available(department, date):
                    continue
                    
                # Get available rooms for this date and session
                available_rooms = self._get_available_rooms_for_exam(rooms_needed, date, session)
                if len(available_rooms) < rooms_needed:
                    continue
                    
                # Get available invigilators for this date and session
                available_invigilators = self._get_available_invigilators_for_exam(rooms_needed, date, session)
                if len(available_invigilators) < rooms_needed:
                    continue
                    
                # If we get here, we have all required resources
                return self._format_schedule({
                    'date': date,
                    'session': session,
                    'rooms': available_rooms[:rooms_needed],
                    'invigilators': available_invigilators[:rooms_needed]
                }, subject_code, subject_title, semester, department, num_students, rooms_needed)
        
        return None

    def _format_schedule(self, solution, subject_code, subject_title, semester, department, num_students, rooms_needed):
        """Format the solution into a schedule dictionary"""
        schedule = []
        students_per_room = num_students // rooms_needed
        remaining_students = num_students % rooms_needed
        
        for i in range(rooms_needed):
            # Distribute students evenly across rooms
            room_students = students_per_room + (1 if i < remaining_students else 0)
            
            schedule.append({
                'subject_code': subject_code,
                'subject_title': subject_title,
                'semester': semester,
                'department': department,
                'date': solution['date'],
                'session': solution['session'],
                'room_code': solution['rooms'][i],
                'invigilator_code': solution['invigilators'][i],
                'student_count': room_students
            })
        return schedule

    def save_schedule(self, schedule):
        """Save schedule to database with transaction"""
        conn = create_connection(self.db_file)
        if not conn:
            return False
            
        try:
            cur = conn.cursor()
            
            # Start transaction
            cur.execute("BEGIN TRANSACTION")
            
            # Add subject if new
            exam = schedule[0]
            cur.execute("""
                INSERT OR IGNORE INTO subjects 
                (code, title, semester, department_code)
                VALUES (?, ?, ?, ?)
            """, (
                exam['subject_code'], exam['subject_title'],
                exam['semester'], exam['department']
            ))
            
            # Add all exam slots
            for exam in schedule:
                cur.execute("""
                    INSERT INTO exam_schedule 
                    (date, session, subject_code, invigilator_id, room_code)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    exam['date'], exam['session'],
                    exam['subject_code'], exam['invigilator_code'],
                    exam['room_code']
                ))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

    def get_full_schedule(self):
        """Get complete exam schedule with all details"""
        conn = create_connection(self.db_file)
        if not conn:
            return []
            
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT es.date, es.session, es.subject_code, s.title as subject_title,
                       d.name as department, s.semester, 
                       u.name as invigilator_name, es.room_code
                FROM exam_schedule es
                JOIN subjects s ON es.subject_code = s.code
                JOIN departments d ON s.department_code = d.code
                JOIN users u ON es.invigilator_id = u.id
                ORDER BY es.date, es.session, es.room_code
            """)
            
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
            
        except sqlite3.Error as e:
            print(f"Error loading full schedule: {e}")
            return []
        finally:
            conn.close()

    def export_schedule_to_csv(self):
        """Export schedule to CSV format"""
        schedule = self.get_full_schedule()
        if not schedule:
            return None
            
        df = pd.DataFrame(schedule)
        return df.to_csv(index=False)

    def export_schedule_to_excel(self):
        """Export schedule to Excel format"""
        schedule = self.get_full_schedule()
        if not schedule:
            return None
            
        df = pd.DataFrame(schedule)
        return df.to_excel(index=False)


def view_schedule(db_file):
    """View and export the current exam schedule"""
    st.subheader("Current Exam Schedule")
    
    scheduler = ExamScheduler(db_file)
    schedule = scheduler.get_full_schedule()
    
    if schedule:
        # Display as table
        df = pd.DataFrame(schedule)
        st.dataframe(df)
        
        # Export options
        st.subheader("Export Schedule")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Download as CSV"):
                csv = scheduler.export_schedule_to_csv()
                st.download_button(
                    label="Click to download",
                    data=csv,
                    file_name="exam_schedule.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("Download as Excel"):
                excel = scheduler.export_schedule_to_excel()
                st.download_button(
                    label="Click to download",
                    data=excel,
                    file_name="exam_schedule.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.info("No exams scheduled yet")


