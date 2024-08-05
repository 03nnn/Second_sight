import cv2
from flask import Flask, render_template, Response
from webcamvideostream import WebcamVideoStream
from flask_basicauth import BasicAuth
import time
import threading
import subprocess
import RPi.GPIO as GPIO
import os
import signal

app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = 'SecondSight'
app.config['BASIC_AUTH_PASSWORD'] = 'system'
app.config['BASIC_AUTH_FORCE'] = True

basic_auth = BasicAuth(app)

@app.route('/')
@basic_auth.required
def index():
    return render_template('index.html')

def gen(camera):
    while True:
        if camera.stopped:
            break

        frame = camera.read()

        # Check if the frame is not None and not empty
        if frame is not None and frame.size != 0:
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
            else:
                print("Error encoding frame")
        else:
            print("Frame is None or empty")

@app.route('/video_feed')
def video_feed():
    return Response(gen(WebcamVideoStream().start()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
        app.run(host='0.0.0.0', debug=True, threaded=True)
