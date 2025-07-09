import cv2
import face_recognition
import numpy as np
import os
import time
from database import Database
from utils import save_student_image

class StudentRegistration:
    def __init__(self, db_connection=None):
        self.db = db_connection if db_connection else Database()
        self.num_images = 20  # Number of images to capture
        self.image_folder = "data/student_images"
        
        # Create folder if it doesn't exist
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
    
    def register_with_multiple_images(self, student_id, name, department):
        """Register a student by capturing multiple images"""
        print(f"Starting multi-image registration for student {student_id}: {name}")
        print(f"Will capture {self.num_images} images - please rotate your face slowly in different angles")
        print("Press 's' to start the capture sequence, 'q' to quit")
        
        # Initialize webcam
        cap = cv2.VideoCapture(0)
        
        # Set higher resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Wait for user to press 's' to start
        start_capture = False
        
        face_encodings = []
        captured_images = 0
        last_capture_time = 0
        capture_interval = 1.0  # Seconds between captures
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Display instructions on frame
            instruction_text = "Press 's' to start, 'q' to quit"
            if start_capture:
                instruction_text = f"Capturing images: {captured_images}/{self.num_images} - Move your face slowly"
            
            cv2.putText(frame, instruction_text, (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display image count
            if start_capture:
                cv2.putText(frame, f"Images: {captured_images}/{self.num_images}", 
                           (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display frame
            cv2.imshow('Student Registration - Multiple Angles', frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            # Start capture sequence on 's' key
            if key == ord('s'):
                start_capture = True
                print("Starting capture sequence...")
                last_capture_time = time.time() - capture_interval  # Allow immediate first capture
            
            # Quit on 'q' key
            elif key == ord('q'):
                print("Registration cancelled")
                break
            
            # If capture sequence started and interval time passed
            if start_capture and time.time() - last_capture_time >= capture_interval:
                # Find face locations
                face_locations = face_recognition.face_locations(frame)
                
                if len(face_locations) == 0:
                    print("No face detected. Please face the camera.")
                    continue
                
                if len(face_locations) > 1:
                    print("Multiple faces detected. Please ensure only one face is in the frame.")
                    continue
                
                # Extract face encoding
                current_face_encodings = face_recognition.face_encodings(frame, face_locations)
                
                if current_face_encodings:
                    # Save the encoding
                    face_encodings.append(current_face_encodings[0])
                    
                    # Save face image with better cropping
                    face_location = face_locations[0]
                    top, right, bottom, left = face_location
                    
                    # Add some margin to the face crop (20% of face size)
                    height = bottom - top
                    width = right - left
                    margin_h = int(height * 0.2)
                    margin_w = int(width * 0.2)
                    
                    # Ensure margins stay within image boundaries
                    top = max(0, top - margin_h)
                    bottom = min(frame.shape[0], bottom + margin_h)
                    left = max(0, left - margin_w)
                    right = min(frame.shape[1], right + margin_w)
                    
                    face_image = frame[top:bottom, left:right]
                    image_path = os.path.join(self.image_folder, f"{student_id}_{captured_images+1}.jpg")
                    cv2.imwrite(image_path, face_image)
                    
                    print(f"Captured image {captured_images+1}/{self.num_images}")
                    captured_images += 1
                    last_capture_time = time.time()
                    
                    # Check if we've captured enough images
                    if captured_images >= self.num_images:
                        print(f"Captured {captured_images} images successfully")
                        break
                else:
                    print("Failed to encode face. Please try again.")
        
        # Release resources
        cap.release()
        cv2.destroyAllWindows()
        
        # Register student with all face encodings if we captured any
        if len(face_encodings) > 0:
            result = self.db.register_student(student_id, name, department, face_encodings)
            print(result)
            print(f"Registered student with {len(face_encodings)} different face angles")
            return True
        else:
            print("No face encodings captured. Registration failed.")
            return False
    
    def register_from_camera(self, student_id, name, department):
        """Legacy method for single image registration"""
        print(f"Starting registration for student {student_id}: {name}")
        print("Press 'c' to capture image when ready, 'q' to quit")
        
        # Initialize webcam
        cap = cv2.VideoCapture(0)
        
        # Set higher resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Display frame
            cv2.imshow('Registration - Press c to capture', frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            # Capture image on 'c' key
            if key == ord('c'):
                # Find face locations
                face_locations = face_recognition.face_locations(frame)
                
                if len(face_locations) == 0:
                    print("No face detected. Please try again.")
                    continue
                
                if len(face_locations) > 1:
                    print("Multiple faces detected. Please ensure only one face is in the frame.")
                    continue
                
                # Extract face encoding
                face_encodings = face_recognition.face_encodings(frame, face_locations)
                
                if face_encodings:
                    face_encoding = face_encodings[0]
                    
                    # Save face image with better cropping
                    face_location = face_locations[0]
                    top, right, bottom, left = face_location
                    
                    # Add margin to the face crop (20% of face size)
                    height = bottom - top
                    width = right - left
                    margin_h = int(height * 0.2)
                    margin_w = int(width * 0.2)
                    
                    # Ensure margins stay within image boundaries
                    top = max(0, top - margin_h)
                    bottom = min(frame.shape[0], bottom + margin_h)
                    left = max(0, left - margin_w)
                    right = min(frame.shape[1], right + margin_w)
                    
                    face_image = frame[top:bottom, left:right]
                    image_path = os.path.join(self.image_folder, f"{student_id}_single.jpg")
                    cv2.imwrite(image_path, face_image)
                    
                    # Register student in database
                    result = self.db.register_student(student_id, name, department, [face_encoding])
                    print(result)
                    print(f"Face image saved to {image_path}")
                    break
                else:
                    print("Failed to encode face. Please try again.")
            
            # Quit on 'q' key
            elif key == ord('q'):
                print("Registration cancelled")
                break
        
        # Release resources
        cap.release()
        cv2.destroyAllWindows()
        return True

# Example usage
if __name__ == "__main__":
    registration = StudentRegistration()
    # registration.register_with_multiple_images("S12345", "John Doe", "Computer Science")