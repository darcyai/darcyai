# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

import cv2

from darcyai.input.camera_stream import CameraStream
from darcyai.output.live_feed_stream import LiveFeedStream
from darcyai.pipeline import Pipeline
from darcyai.config import RGB

from darcyai.perceptor.processor import Processor
from darcyai.perceptor.people_perceptor import PeoplePerceptor

#Create a callback function for handling the input that is about to pass to the People Perceptor
def people_input_callback(input_data, pom, config):
    #Just take the frame from the incoming Input Stream and send it onward - no need to modify the frame
    frame = input_data.data.copy()
    return frame

#Create a callback function for handling the Live Feed output stream data before it gets presented
def live_feed_callback(pom, input_data):
    #Start wth the annotated video frame available from the People Perceptor
    frame = pom.peeps.annotatedFrame().copy()

    #Add some text telling how many people are in the scene
    label = "{} peeps".format(pom.peeps.peopleCount())
    color = (0, 255, 0)
    cv2.putText(frame, str(label), (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    #If we have anyone, demonstrate looking up that person in the POM by getting their face size
    #And then put it on the frame as some text
    #NOTE: this will just take the face size from the last person in the array
    if pom.peeps.peopleCount() > 0:
        for person_id in pom.peeps.people():
            face_size = pom.peeps.faceSize(person_id)
            if face_size == 0:
                continue

            face_height = face_size[1]
            label2 = "{} face height".format(face_height)
            color = (0, 255, 255)
            cv2.putText(frame, str(label2), (0, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    #Pass the finished frame out of this callback so the Live Feed output stream can display it
    return frame

#Create a callback function for handling the "New Person" event from the People Perceptor
#Just print the person ID to the console
def new_person_callback(person_id):
    print("New person: {}".format(person_id))

#Instantiate an Camera Stream input stream object
camera = CameraStream(video_device="/dev/video0", fps=20)

#Instantiate the Pipeline object and pass it the Camera Stream object as its input stream source
pipeline = Pipeline(input_stream=camera)

#Create a Live Feed output stream object and specify some URL parameters
live_feed = LiveFeedStream(path="/", port=3456, host="0.0.0.0")

#Add the Live Feed output stream to the Pipeline and use the callback from above as the handler
pipeline.add_output_stream("output", live_feed_callback, live_feed)

#Instantiate a People Perceptor
people_ai = PeoplePerceptor([Processor.CORAL_EDGE_TPU, Processor.CPU], num_cpu_threads=2)
#Subscribe to the "New Person" event from the People Perceptor and use our callback from above as the handler
people_ai.on("new_person_entered_scene", new_person_callback)

#Add the People Perceptor instance to the Pipeline and use the input callback from above as the input preparation handler
pipeline.add_perceptor("peeps", people_ai, input_callback=people_input_callback)

#Update the configuration of the People Perceptor to show the pose landmark dots on the annotated video frame
pipeline.set_perceptor_config("peeps", "show_pose_landmark_dots", True)
pipeline.set_perceptor_config("peeps", "pose_landmark_dot_size", 2)
pipeline.set_perceptor_config("peeps", "pose_landmark_dot_color", RGB(0, 255, 0))
pipeline.set_perceptor_config("peeps", "show_body_rectangle", True)
pipeline.set_perceptor_config("peeps", "show_face_rectangle", True)
pipeline.set_perceptor_config("peeps", "show_person_id", True)
pipeline.set_perceptor_config("peeps", "person_data_identity_text_font_size", 0.5)
pipeline.set_perceptor_config("peeps", "person_data_identity_text_font_size", 0.5)

#Start the Pipeline
pipeline.run()
