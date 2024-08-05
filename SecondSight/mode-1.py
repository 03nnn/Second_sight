import RPi.GPIO as GPIO
import time
import cv2
import numpy as np
import math
from picamera2 import Picamera2
import pyttsx3
import os
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import threading

GPIO.setmode(GPIO.BCM)

util_pin = 24
GPIO.setup(util_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

start = None
length= 0

def util_button_pressed(channel):
    global start, length, t, mic_input_thread
    # Check if the button is currently pressed
    utilbtn = GPIO.input(util_pin)
    
    if utilbtn == GPIO.LOW:
        start = time.time()
        time.sleep(0.2)

        while GPIO.input(util_pin) == GPIO.LOW:
            time.sleep(0.01)
        length = time.time() - start
        
        
        # Check if the press duration has exceeded the long press threshold
        if length >= 2:
            # Reset the mic input thread and t
            if mic_input_thread and mic_input_thread.is_alive():
                mic_input_thread.join()  # Wait for the thread to finish
            t = None
            print("Audio input result reset to None")

            
        if length < 2:
            mic_input_thread = threading.Thread(target=micinput_async)
            mic_input_thread.start()

        start = None
        length = 0
     
    # Button released
   
GPIO.add_event_detect(util_pin, GPIO.FALLING, util_button_pressed, bouncetime=300)

classNames = []

classFile = "/home/SecondSight/project/coco.names"
with open(classFile, "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

configPath = "/home/SecondSight/project/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "/home/SecondSight/project/frozen_inference_graph.pb"

net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)
# Initialize text-to-speech engine with espeak
engine = pyttsx3.init('espeak')

lower_range=np.array([11,88,106])
upper_range=np.array([50,159,235])
ref_width = 20.0
ref_distance=60.0
mic_input_result=None

def obj_data(img):
     obj_width = 0
     hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
     mask=cv2.inRange(hsv,lower_range,upper_range)
     _,mask1=cv2.threshold(mask,254,255,cv2.THRESH_BINARY)
     cnts,_=cv2.findContours(mask1,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
     for c in cnts:
        x=600
        if cv2.contourArea(c)>x:
            x,y,w,h=cv2.boundingRect(c)
            cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
            obj_width = w
     return obj_width

def FocalLength(measured_distance, real_width ,width_in_rf_img):
    focal_length=(width_in_rf_img*measured_distance)/real_width
    return focal_length
    
def calculate_distance(focal_length, real_width, width_in_frame):
    distance=(real_width * focal_length) / (width_in_frame)
    return distance

ref_img = cv2.imread('/home/SecondSight/project/ref.png')

ref_image_width=obj_data(ref_img)
focal_length_found=FocalLength(ref_distance, ref_width, ref_image_width)
print(focal_length_found)

def determine_position(frame, box):
    frame_center_x = frame.shape[1] // 2
    object_x_center = (box[0] + box[2]) // 2
    if object_x_center < frame_center_x:
        return "left"
    else:
        return "right"

def alert_user(className, distance,position, min_distance=30):
    if distance < min_distance:
        alert_text = f"Carefull! {className} is on your {position}."
        print(alert_text)
        engine.say(alert_text)
        engine.runAndWait()

def alert(className, distance,position):
        distance=round(distance,1)
        alert_text = f"The {className} is on your {position} {distance:.2f} centimeters away"
        print(alert_text)
        engine.say(alert_text)
        engine.runAndWait()

def get_nearest_objects(frame, thres, nms,target_class, max_objects=4, min_distance=30):
    classIds, confs, bbox = net.detect(frame, confThreshold=thres, nmsThreshold=nms)
    
    object_info = []
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            # Calculate the distance to the object 
            pixel_width = abs(box[2]-box[0])+0.1
            distance = calculate_distance(focal_length_found,ref_width, pixel_width)
            position=determine_position(frame,box)
            if className == target_class:
                detect_traffic_light(frame)
                break
            
            object_info.append([box, className, distance])
            
            # Sort by distance
            object_info = sorted(object_info, key=lambda x: x[2])
            
            # Limit the number of objects to max_objects
            object_info = object_info[:max_objects]
            
    return object_info
    
prev_color=None
def detect_traffic_light(frame):
    global prev_color

    # Convert the image to the HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define the color ranges for traffic lights
    lower_red = np.array([0, 100, 100])
    upper_red = np.array([10, 255, 255])

    lower_green = np.array([35, 100, 100])
    upper_green = np.array([85, 255, 100])

    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([30, 255, 255])

    # Threshold the image to find red, green, and yellow regions
    mask_red = cv2.inRange(hsv, lower_red, upper_red)
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # Check which color has the most pixels
    red_pixel_count = cv2.countNonZero(mask_red)
    green_pixel_count = cv2.countNonZero(mask_green)
    yellow_pixel_count = cv2.countNonZero(mask_yellow)

    if red_pixel_count > green_pixel_count and red_pixel_count > yellow_pixel_count:
        color = "red"
    elif green_pixel_count > red_pixel_count and green_pixel_count > yellow_pixel_count:
        color = "green"
    elif yellow_pixel_count > red_pixel_count and yellow_pixel_count > green_pixel_count:
        color = "yellow"
    else:
        color = "unknown"
  
    if prev_color==color:
        pass
    else:
        prev_color=color
        play_audio=f"The traffic light is {color}"
        print(play_audio)
        engine.say(play_audio)
        engine.runAndWait()

def record_audio(duration, sample_rate=44100, channels=1):
    try:
        print("Recording...")
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels, dtype=np.int16)
        sd.wait()
        print("Recording complete.")
        return audio_data
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def convert_audio_to_text(audio_data):
    recognizer = sr.Recognizer()
    audio_signal = sr.AudioData(audio_data.tobytes(), sample_rate=44100, sample_width=2)  # Assuming 16-bit PCM encoding

    try:
        text = recognizer.recognize_google(audio_signal)
        return text
    except sr.UnknownValueError:
        print("Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
    
    return None

def micinput_async():
    global mic_input_result
    duration = 5
    sample_rate = 44100
    channels = 1

    audio_data = record_audio(duration, sample_rate, channels)

    if audio_data is not None:
        text_result = convert_audio_to_text(audio_data)
        if text_result:
            mic_input_result=' '.join(text_result.split()[:2]).lower()
        else:
            print("Speech-to-text conversion failed.")
            

if __name__ == "__main__":
    piCam = Picamera2()
    piCam.preview_configuration.main.size = (480, 480)
    piCam.preview_configuration.main.format = "RGB888"
    piCam.preview_configuration.align()
    piCam.configure("preview")
    piCam.start()
    t=None
    prev_class_name=None
    mic_input_thread=None
    while True:
        frame = piCam.capture_array()
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        key=cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        # Check if the micinput thread has finished
        if mic_input_thread and not mic_input_thread.is_alive():
            t = mic_input_result
            print(f"Searching for: {t}")
            mic_input_thread = None  

        object_info = get_nearest_objects(frame, 0.6, 0.05,target_class='traffic light')
        if object_info is not None:
            # Draw rectangles and labels on the frame
             for box, className, distance in object_info:
                 position=determine_position(frame,box)
                 cv2.rectangle(frame, box, color=(0, 255, 0), thickness=1)
                 label = f"{className.upper()} ({distance:.2f} cm)"
                 cv2.putText(frame, label, (box[0] + 10, box[1] + 30), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                 if className == t:
                     alert(t,distance,position)
                     
                 if className == prev_class_name:
                    continue  # Skip alert if it's the same class as the previous one
                 else:
                    prev_class_name = className
                    alert_user(className, distance,position, 30)

       
        cv2.imshow("Output", frame)
        

        
              
    cv2.destroyAllWindows()
    GPIO.cleanup()
