Command to run the Attendance system 

1. Register Students with Multiple Angle Captures apprrox 20 Images
   python app.py --mode register --student_id S12345 --name "John Doe" --department "Computer Science" --multi_capture

2. Start a Lecture and Track Attendance and it create a lecture entry int he mongodb as well
   python app.py --mode lecture --lecture_id MATH101_23MAR --course "MATH101" --instructor "Dr. Johnson" --room "B-201"

3. View Regular Attendance (Without Lecture)
    python app.py --mode recognize

