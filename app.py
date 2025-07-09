import argparse
import os
from database import Database
from register import StudentRegistration
from recognize import FaceRecognitionAttendance

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Smart Attendance System')
    parser.add_argument('--mode', type=str, default='recognize',
                      help='Mode: register, recognize, or lecture')
    parser.add_argument('--student_id', type=str, default=None,
                      help='Student ID for registration')
    parser.add_argument('--name', type=str, default=None,
                      help='Student Name for registration')
    parser.add_argument('--department', type=str, default=None,
                      help='Student Department for registration')
    parser.add_argument('--multi_capture', action='store_true',
                      help='Capture multiple face angles during registration')
    parser.add_argument('--lecture_id', type=str, default=None,
                      help='Lecture ID for attendance tracking')
    parser.add_argument('--course', type=str, default=None,
                      help='Course code for the lecture')
    parser.add_argument('--instructor', type=str, default=None,
                      help='Instructor name for the lecture')
    parser.add_argument('--room', type=str, default=None,
                      help='Room number for the lecture')
    
    args = parser.parse_args()
    
    # Initialize database connection
    db = Database()
    
    if args.mode == 'register':
        # Check required arguments
        if not args.student_id or not args.name or not args.department:
            print("Error: student_id, name, and department are required for registration")
            print("Example: python app.py --mode register --student_id S12345 --name 'John Doe' --department 'Computer Science'")
            return
        
        # Initialize registration module
        registration = StudentRegistration(db)
        
        if args.multi_capture:
            # Register with multiple face angles
            success = registration.register_with_multiple_images(args.student_id, args.name, args.department)
            if success:
                print(f"Successfully registered student {args.student_id} with multiple face angles")
            else:
                print(f"Failed to register student {args.student_id}")
        else:
            # Register with single image
            success = registration.register_from_camera(args.student_id, args.name, args.department)
            if success:
                print(f"Successfully registered student {args.student_id}")
            else:
                print(f"Failed to register student {args.student_id}")
    
    elif args.mode == 'lecture':
        # Create new lecture for attendance tracking
        if not args.lecture_id or not args.course or not args.instructor or not args.room:
            print("Error: lecture_id, course, instructor, and room are required to create a lecture")
            print("Example: python app.py --mode lecture --lecture_id L001 --course CS101 --instructor 'Dr. Smith' --room 'A-101'")
            return
        
        # Create the lecture in database
        result = db.create_lecture(args.lecture_id, args.course, args.instructor, args.room)
        print(result)
        
        # Start recognition for this lecture
        recognition = FaceRecognitionAttendance(db, args.lecture_id)
        recognition.start_recognition()
        
        # End the lecture when recognition finishes
        db.end_lecture(args.lecture_id)
        print(f"Ended lecture {args.lecture_id}")
    
    elif args.mode == 'recognize':
        # Regular attendance recognition (not lecture-specific)
        recognition = FaceRecognitionAttendance(db, args.lecture_id)
        recognition.start_recognition()
    
    else:
        print(f"Unknown mode: {args.mode}")
        print("Available modes: register, recognize, lecture")

if __name__ == "__main__":
    main()