import cv2
import face_recognition
import numpy as np
import time
from datetime import datetime
from database import Database
from utils import draw_box_with_name

class FaceRecognitionAttendance:
    def __init__(self, db_connection=None, lecture_id=None):
        self.db = db_connection if db_connection else Database()
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        self.marked_students = set()  # Keep track of students already marked
        self.last_marked_time = {}    # Track time to avoid duplicate marking
        self.cooldown_seconds = 60    # Wait time before remarking the same student
        self.lecture_id = lecture_id  # Current lecture ID for attendance
        
        # Load student data from database
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load known face encodings from database"""
        students = self.db.get_all_student_encodings()
        
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        
        for student in students:
            # In real application, convert stored list back to numpy array
            face_encoding = np.array(student["face_encoding"])
            self.known_face_encodings.append(face_encoding)
            self.known_face_ids.append(student["student_id"])
            self.known_face_names.append(student["name"])
        
        print(f"Loaded {len(students)} student face encodings")
    
    def start_recognition(self, camera_source=0, recognition_interval=1.0):
        """Start face recognition from webcam"""
        # Initialize webcam
        cap = cv2.VideoCapture(camera_source)
        
        # Set higher resolution - try different resolutions based on your camera
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Variables for processing speed
        frame_count = 0
        
        # Store previous face locations and IDs to prevent flashing
        prev_face_locations = []
        prev_face_ids = []
        prev_face_names = []
        
        print("Starting face recognition attendance system...")
        print("Press 'q' to quit")
        
        # Reset marked students for new session
        self.marked_students = set()
        
        if not self.lecture_id:
            # Generate lecture ID if not provided
            self.lecture_id = f"L_{datetime.now().strftime('%Y%m%d_%H%M')}"
            print(f"Generated Lecture ID: {self.lecture_id}")
        
        while True:
            # Grab a single frame
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Make a copy for display (we'll keep full resolution)
            display_frame = frame.copy()
            
            # Convert from BGR color (OpenCV) to RGB (face_recognition)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process only every few frames to save CPU
            process_this_frame = frame_count % int(recognition_interval * 30) == 0
            
            if process_this_frame:
                # Find face locations and encodings
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                face_ids = []
                face_names = []
                
                # Check each face against known faces
                for face_encoding in face_encodings:
                    # Compare with known faces
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.5)
                    
                    student_id = "Unknown"
                    name = "Unknown"
                    
                    # Use the known face with the smallest distance to the new face
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        # Only accept matches with distance below threshold
                        if matches[best_match_index] and face_distances[best_match_index] < 0.5:
                            student_id = self.known_face_ids[best_match_index]
                            name = self.known_face_names[best_match_index]
                            
                            # Mark attendance with cooldown to avoid duplicate marking
                            current_time = time.time()
                            is_already_marked = False
                            
                            if student_id in self.marked_students:
                                is_already_marked = True
                            
                            if student_id not in self.last_marked_time or \
                               (current_time - self.last_marked_time[student_id] > self.cooldown_seconds):
                                # Mark attendance in database
                                if not is_already_marked:
                                    result = self.db.mark_attendance(student_id, self.lecture_id)
                                    print(f"{result} at {time.strftime('%H:%M:%S')}")
                                    
                                    # Update last marked time
                                    self.last_marked_time[student_id] = current_time
                                    self.marked_students.add(student_id)
                                else:
                                    print(f"Already marked attendance for {name} ({student_id})")
                    
                    face_ids.append(student_id)
                    face_names.append(name)
                
                # Update previous data
                prev_face_locations = face_locations
                prev_face_ids = face_ids
                prev_face_names = face_names
            
            # Always draw using the most recent detection results, prevents flashing
            for (top, right, bottom, left), student_id, name in zip(prev_face_locations, prev_face_ids, prev_face_names):
                # Draw box and name on frame
                if student_id != "Unknown":
                    label = f"{name} ({student_id})"
                    
                    # Add "Already marked" indicator
                    if student_id in self.marked_students:
                        label += " - Already marked"  # Changed from "✓" to text
                    color = (0, 255, 0)  # Green for recognized faces
                else:
                    label = "Unknown"
                    color = (0, 0, 255)  # Red for unknown faces
                
                # Scale coordinates if needed for display frame
                draw_box_with_name(display_frame, (top, right, bottom, left), label,color)
            
            # Display the resulting image (full resolution)
            cv2.imshow('Face Recognition Attendance System', display_frame)
            
            # Hit 'q' on the keyboard to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            frame_count += 1
        
        # Release resources
        cap.release()
        cv2.destroyAllWindows()
        
        # Print summary
        print("\nAttendance Summary for Lecture:", self.lecture_id)
        print(f"Total students marked present: {len(self.marked_students)}")
        for student_id in self.marked_students:
            index = self.known_face_ids.index(student_id)
            name = self.known_face_names[index]
            print(f"- {name} ({student_id})")

# Example usage
if __name__ == "__main__":
    recognizer = FaceRecognitionAttendance(lecture_id="LECTURE_001")
    recognizer.start_recognition()