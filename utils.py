import os
import cv2
import numpy as np
import pickle
from datetime import datetime

def save_encoding(student_id, encoding, folder="data/encodings"):
    """Save face encoding to a file"""
    # Create folder if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # Save encoding as pickle file
    file_path = os.path.join(folder, f"{student_id}.pkl")
    with open(file_path, 'wb') as file:
        pickle.dump(encoding, file)
    
    return file_path

def load_encoding(student_id, folder="data/encodings"):
    """Load face encoding from a file"""
    file_path = os.path.join(folder, f"{student_id}.pkl")
    
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'rb') as file:
        encoding = pickle.load(file)
    
    return encoding

def save_student_image(student_id, image, folder="data/student_images"):
    """Save student face image"""
    # Create folder if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # Save image
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(folder, f"{student_id}_{timestamp}.jpg")
    cv2.imwrite(file_path, image)
    
    return file_path

def resize_frame(frame, scale=0.5):
    """Resize frame for faster processing"""
    width = int(frame.shape[1] * scale)
    height = int(frame.shape[0] * scale)
    return cv2.resize(frame, (width, height))

def draw_box_with_name(frame, location, name, color=(0, 255, 0)):
    """Draw bounding box and name on the frame"""
    top, right, bottom, left = location
    
    # Draw box
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
    
    # Draw label background
    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
    
    # Put text
    cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    return frame