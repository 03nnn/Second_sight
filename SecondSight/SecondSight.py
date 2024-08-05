import RPi.GPIO as GPIO
import time

#mode1 imports
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

#mode2 imports
import cv2
import time
from picamera2 import Picamera2
import pytesseract
import os
import pyttsx3

#mode3 imports
import webbrowser
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import threading

#mode3 imports 2
import cv2
import sys
from flask import Flask, render_template, Response
from webcamvideostream import WebcamVideoStream
from flask_basicauth import BasicAuth
import time
import threading
import signal

# Set the GPIO mode
GPIO.setmode(GPIO.BCM)

# Define GPIO pin for the button
mode_pin = 4
#util_pin = 24
#pwr_pin = 12
#powerpin= xx
#utilitypin = 18

# Setup the button as input with a pull-up resistor
GPIO.setup(mode_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#GPIO.setup(util_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#GPIO.setup(pwr_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

modebtn = GPIO.input(mode_pin)
#utilbtn = GPIO.input(util_pin)
#pwrbrn = GPIO.input(pwr_pin)


mode_no = 0

#code
def button_pressed(channel):
	# Take the desired action here
    print("Button pressed!")
    global mode_no 
    mode_no= (mode_no + 1) % 3
    time.sleep(1)  # Add a delay to prevent multiple calls
    return
    
GPIO.add_event_detect(mode_pin, GPIO.FALLING, button_pressed, bouncetime=300)

#the functions that will interupt and move to next mode
    
def mode1():
	try:
		process = subprocess.Popen(["python", "mode-1.py"])
		#subprocess.run(["python", "mode-3-stream.py"], check=True)
	except subprocess.CalledProcessError as e:
		print(f"Error: {e}")
	finally:
		while True:
			if mode_no == 1 or mode_no == 2:
				print("terminate")
				process.terminate()
				time.sleep(1)
				break

def mode2():
	try:
		process = subprocess.Popen(["python", "mode-2.py"])
		#subprocess.run(["python", "mode-3-stream.py"], check=True)
	except subprocess.CalledProcessError as e:
		print(f"Error: {e}")
	finally:
		while True:
			if mode_no == 0 or mode_no == 2:
				print("terminate")
				process.terminate()
				time.sleep(1)
				break
				
process=None

def mode3_2():
	GPIO.setmode(GPIO.BCM)
	util_pin = 24
	GPIO.setup(util_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	start = None
	length = 0
	

	def util2_button_pressed(channel):
		global start, length, process

		utilbtn = GPIO.input(util_pin)

		if utilbtn == GPIO.LOW:
			start = time.time()
			time.sleep(0.2)

			while GPIO.input(util_pin) == GPIO.LOW:
				time.sleep(0.01)
			length = time.time() - start

			if length >= 2:
				print("Ending call")
				if process and process.poll() is None:
					os.killpg(os.getpgid(process.pid), signal.SIGTERM)
					time.sleep(0.2)
					# time.sleep(2)

			if length < 2:
				try:
					print("Calling")
					if process and process.poll() is None:
						print("Previous process is still running.")
						return  # Exit the function without starting a new subprocess
					process = subprocess.Popen(["python", "mode_3_call.py"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn=os.setsid)
					
				except subprocess.CalledProcessError as e:
					print(f"Error: {e}")
					# time.sleep(2)

		start = None
		length=0

	GPIO.add_event_detect(util_pin, GPIO.FALLING, util2_button_pressed, bouncetime=300)
	try:
		process = subprocess.Popen(["python", "mode-3-stream.py"])
		#subprocess.run(["python", "mode-3-stream.py"], check=True)
	except subprocess.CalledProcessError as e:
		print(f"Error: {e}")
	finally:
		while True:
			if mode_no == 0 or mode_no == 1:
				print("terminate")
				process.terminate()
				time.sleep(1)
				break
				


try:
	while True:
		if mode_no == 0:
			print("mode-1",mode_no)
			mode1()
		elif mode_no == 1:
			print("mode-2",mode_no)
			mode2()
		elif mode_no == 2:
			print("mode-3",mode_no)
			mode3_2()
			
except KeyboardInterrupt:
    print("Button press detected. Exiting function...")
    time.sleep(1)
    GPIO.cleanup()
    sys.exit()

GPIO.cleanup()
