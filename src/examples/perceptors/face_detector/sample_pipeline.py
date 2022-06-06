# Copyright 2022 Edgeworx, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#Add libraries that we need, including Numpy and OpenCV
import cv2
import numpy as np
import threading
from flask import Flask

#Add Darcy AI libraries that we need, particularly CameraStream, LiveFeedStream, and Pipeline
from darcyai.input.camera_stream import CameraStream
from darcyai.output.live_feed_stream import LiveFeedStream
from darcyai.pipeline import Pipeline

#Add our custom face detector Perceptor class
from coral_face_detector import CoralFaceDetector

#Define a class to hold our demo application
class SamplePipeline():
    def __init__(self):
        #Use the CameraStream input stream
        camera = CameraStream(video_device="/dev/video0", fps=20)

        #Set up a Flask app so we can host a live video stream viewing UI and a configuration REST API
        self.__flask_app = Flask(__name__)
        
        #Create a Darcy AI pipeline that uses the Flask app and our camera input stream
        self.__pipeline = Pipeline(input_stream=camera,
                                   universal_rest_api=True,
                                   rest_api_flask_app=self.__flask_app,
                                   rest_api_base_path="/pipeline")

        #Set up a live video feed output stream and add it to the pipeline
        live_feed = LiveFeedStream(
            flask_app=self.__flask_app, path="/live-stream")
        self.__pipeline.add_output_stream(
            "live_feed", self.__live_feed_callback, live_feed)

        #Create an instance of the face detector Perceptor and add it to the pipeline
        face_detector = CoralFaceDetector(threshold=0.9)
        self.__pipeline.add_perceptor(
            "face", face_detector, input_callback=self.__face_input_callback)

    #Define our "run" method which just calls "run" on the pipeline but also starts our Flask app on port 8080 for the REST API
    def run(self):
        threading.Thread(
            target=self.__flask_app.run,
            kwargs={"host": "0.0.0.0", "port": 8080, "debug": False}).start()

        self.__pipeline.run()

    #Define a callback for working with the live feed
    #Take the incoming data which is a video frame and draw rectangles on the faces
    def __live_feed_callback(self, pom, input_data):
        frame = input_data.data.copy()

        for face in pom.face:
            cv2.rectangle(frame, (face.xmin, face.ymin), (face.xmax, face.ymax), (0, 255, 0), 2)

        return frame

    #Define a callback for handling the input that goes into the face detector Perceptor
    #We just need to change the color order of the video frame because our AI model wants RGB instead of BGR
    def __face_input_callback(self, input_data, pom, config):
        frame = input_data.data.copy()
        color_cvt_face = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        return color_cvt_face

#In the main thread, start the application by instantiating our demo class and calling "run"
if __name__ == "__main__":
    sample_pipeline = SamplePipeline()
    sample_pipeline.run()
