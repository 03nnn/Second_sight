import cv2
import time
from picamera2 import Picamera2
import pytesseract
import os
import pyttsx3

# Initialize the camera
piCam = Picamera2()
piCam.preview_configuration.main.size = (480, 480)
piCam.preview_configuration.main.format = "RGB888"
piCam.preview_configuration.align()
piCam.configure("preview")
piCam.start()

# Set the path to the Tesseract executable (replace with the actual path on your Raspberry Pi)
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Initialize the text-to-speech engine
engine = pyttsx3.init()

engine.setProperty('rate', 150) 

def capture_and_process_image():
    engine.say("Three")
    engine.runAndWait()
    engine.say("Two")
    engine.runAndWait()
    engine.say("One")
    engine.runAndWait()
        
    # Capture an image using Picamera
    frame = piCam.capture_array()
    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Save the image to a file
    image_filename = "captured_image.jpg"
    cv2.imwrite(image_filename, frame)


    # Process text from the image using OCR (Tesseract)
    text = pytesseract.image_to_string(image_filename)

    return text

def text_to_speech(text):
    # Convert text to speech
    engine.setProperty('rate', 150) 
    engine.say(text)
    engine.runAndWait()


text_to_speech(capture_and_process_image())



