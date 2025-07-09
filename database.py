import pymongo
from datetime import datetime
import numpy as np

class Database:
    def __init__(self, connection_string="mongodb://localhost:27017/"):
        """Initialize database connection"""
        self.client = pymongo.MongoClient(connection_string)
        self.db = self.client["university_attendance"]
        self.students = self.db["students"]
        self.attendance = self.db["attendance"]
        self.lectures = self.db["lectures"]
    
    def register_student(self, student_id, name, department, face_encodings):
        """Register a new student with face encodings"""
        # If only one encoding is provided, convert to list
        if isinstance(face_encodings, np.ndarray) and face_encodings.ndim == 1:
            face_encodings = [face_encodings]
        
        # Convert all encodings to lists for MongoDB storage
        face_encodings_list = [encoding.tolist() for encoding in face_encodings]
        
        student_data = {
            "student_id": student_id,
            "name": name,
            "department": department,
            "face_encodings": face_encodings_list,
            "registered_on": datetime.now()
        }
        
        # Check if student already exists
        existing = self.students.find_one({"student_id": student_id})
        if existing:
            # Update face encodings
            self.students.update_one(
                {"student_id": student_id},
                {"$set": {
                    "face_encodings": face_encodings_list,
                    "name": name,
                    "department": department
                }}
            )
            return f"Updated face data for student {student_id}"
        else:
            # Insert new student
            self.students.insert_one(student_data)
            return f"Registered student {student_id} successfully"
    
    def add_face_encoding(self, student_id, face_encoding):
        """Add an additional face encoding for an existing student"""
        # Check if student exists
        existing = self.students.find_one({"student_id": student_id})
        if not existing:
            return f"Student {student_id} not found"
        
        # Add new encoding to existing encodings
        self.students.update_one(
            {"student_id": student_id},
            {"$push": {"face_encodings": face_encoding.tolist()}}
        )
        return f"Added new face encoding for student {student_id}"
    
    def get_all_student_encodings(self):
        """Retrieve all student face encodings"""
        students = list(self.students.find({}, {"student_id": 1, "name": 1, "face_encodings": 1}))
        
        # Process students for recognition
        processed_students = []
        
        for student in students:
            # For each encoding of this student, create a recognition entry
            for encoding in student.get("face_encodings", []):
                processed_students.append({
                    "student_id": student["student_id"],
                    "name": student["name"],
                    "face_encoding": np.array(encoding)
                })
        
        return processed_students
    
    def create_lecture(self, lecture_id, course_code, instructor, room, start_time=None):
        """Create a new lecture session"""
        if not start_time:
            start_time = datetime.now()
        
        lecture_data = {
            "lecture_id": lecture_id,
            "course_code": course_code,
            "instructor": instructor,
            "room": room,
            "start_time": start_time,
            "end_time": None,
            "status": "active"
        }
        
        # Check if lecture already exists
        existing = self.lectures.find_one({"lecture_id": lecture_id})
        if existing:
            return f"Lecture {lecture_id} already exists"
        
        # Insert new lecture
        self.lectures.insert_one(lecture_data)
        return f"Created lecture {lecture_id}"
    
    def end_lecture(self, lecture_id):
        """End a lecture session"""
        # Update lecture end time
        self.lectures.update_one(
            {"lecture_id": lecture_id},
            {"$set": {"end_time": datetime.now(), "status": "completed"}}
        )
        return f"Ended lecture {lecture_id}"
    
    def mark_attendance(self, student_id, lecture_id=None):
        """Mark attendance for a student"""
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        
        # If lecture_id not provided, use date-based attendance
        if not lecture_id:
            # Check if attendance already marked today
            existing = self.attendance.find_one({
                "student_id": student_id,
                "date": date_str,
                "lecture_id": None
            })
            
            if existing:
                # Update exit time
                self.attendance.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"exit_time": timestamp}}
                )
                return f"Updated exit time for student {student_id}"
            else:
                # Create new attendance record
                attendance_data = {
                    "student_id": student_id,
                    "date": date_str,
                    "lecture_id": None,
                    "entry_time": timestamp,
                    "exit_time": None,
                    "status": "present"
                }
                self.attendance.insert_one(attendance_data)
                return f"Marked attendance for student {student_id}"
        else:
            # Check if attendance already marked for this lecture
            existing = self.attendance.find_one({
                "student_id": student_id,
                "lecture_id": lecture_id
            })
            
            if existing:
                return f"Already marked attendance for student {student_id} in lecture {lecture_id}"
            else:
                # Create new attendance record
                attendance_data = {
                    "student_id": student_id,
                    "date": date_str,
                    "lecture_id": lecture_id,
                    "timestamp": timestamp,
                    "status": "present"
                }
                self.attendance.insert_one(attendance_data)
                return f"Marked attendance for student {student_id} in lecture {lecture_id}"
    
    def get_attendance_report(self, date=None, lecture_id=None):
        """Get attendance report for a specific date or lecture"""
        query = {}
        
        if date:
            query["date"] = date
        
        if lecture_id:
            query["lecture_id"] = lecture_id
        
        report = list(self.attendance.find(query))
        return report
    
    def get_student_attendance(self, student_id):
        """Get attendance history for a specific student"""
        report = list(self.attendance.find({"student_id": student_id}))
        return report
    
    def close_connection(self):
        """Close the MongoDB connection"""
        self.client.close()