# Building your Darcy AI application

It’s easy to build a Darcy AI application but how do you get started? Here’s an example application that introduces all of the main concepts you will need for building your own application. Start by following along!

## What you will accomplish

This guide will walk you through the creation of a simple yet powerful Darcy AI application. Many of the impressive features of Darcy AI are used here in this simple demo app so you can immediately gain experience working with those features. By the end of this guide you will have built and run your first Darcy AI application in your favorite IDE. After you have successfully accomplished everything in this guide, you should be able to modify the code to customize the application or begin building your own Darcy AI application with a similar structure and level of complexity.

Follow the next step recommended at the bottom of this guide to learn how to package and then deploy your Darcy AI applications. After those steps, you will be ready to learn more advanced Darcy AI app development.

## Requirements

You’ll need to have a few things in place before you build. Here’s the list:
- A laptop or desktop computer running Mac OS X or Windows
- A webcam or USB camera (the built-in webcam on your computer should work nicely)
- Python version 3.6.9 or greater
- An integrated development environment (IDE) for writing and debugging your code
- The Darcy AI Python library and other supporting Python packages
- Docker for Mac, Windows, or Linux depending on your computer

When you are ready to package and deploy your Darcy AI application, try any of the following:
- A Raspberry Pi with an attached video camera (and an optional Google Coral edge TPU for dramatically increased performance)
- An Nvidia Jetson Nano with an attached video camera (and an optional Google Coral edge TPU will increase performance here, too)
- An Intel NUC edge computer with a USB camera
- Any other edge compute board that can receive camera input and runs the Linux operating system

## Environment setup

If you are using a MacOS laptop or desktop, follow the [Mac OS X Environment Setup Guide](../macos-setup/).

If you are using a Windows laptop or desktop, follow the [Windows Environment Setup Guide](../windows-setup/).

You can also use an edge compute board as your development environment. Choose from the following options to set up your edge board instead of your laptop or desktop computer. You do not need to follow these environment setup steps for a Raspberry Pi or Jetson Nano board if you are just using those boards to run your packaged Darcy AI applications.

If you need to setup a Raspberry Pi as a Darcy AI development environment, follow the [Raspberry Pi Environment Setup Guide](../raspberry-pi-setup/).

If you need to setup a Jetson Nano as a Darcy AI development environment, follow the [Jetson Nano Environment Setup Guide](../jetson-nano-setup/).

## Create your application Python file and import libraries

You only need a single Python file to build a Darcy AI application. Open a new .py file in your favorite IDE and name it whatever you want. Then add the following statements at the top to include the Darcy AI libraries and some additional helpful libraries:
```
import cv2
import os
import pathlib

from darcyai.perceptor.people_perceptor import PeoplePerceptor
from darcyai.input.camera_stream import CameraStream
from darcyai.output.live_feed_stream import LiveFeedStream
from darcyai.pipeline import Pipeline
from darcyai.config import RGB
```

If you don’t have the `darcyai` library installed yet, you can install it with PIP package installer for Python using the following commands:
```
pip install darcyai
```

If you have multiple versions of Python on your system, you may need to install the `darcyai` library using the Python3 version of PIP as follows:
```
pip3 install darcyai
```

## Add the [Pipeline, Input Stream, and Output Stream objects](../terminology/)

This part is quite easy. Just follow the comments to learn more about these 3 important lines of code.
```
# Instantiate an Camera Stream input stream object
camera = CameraStream(video_device=0, fps=20)

# Instantiate the Pipeline object and pass it the Camera Stream object as its input stream source
pipeline = Pipeline(input_stream=camera)

# Create a Live Feed output stream object and specify some URL parameters
live_feed = LiveFeedStream(path="/", port=3456, host="0.0.0.0")
```

## Set up a [callback](../terminology/#callback) and add the [Output Stream](../terminology/#output-stream) to the [Pipeline](../terminology/#pipeline)

Before we add the LiveFeed Output Stream to the Pipeline, we need to set up a callback function that we are going to use to process the data before displaying the video. Follow the comments to learn about the steps that are taken. This is the most complex portion of the whole application and it is where all of the business logic is taking place. After the callback function definition, there is a line for adding the LiveFeed Output Stream to the Pipeline. That command needs to have the callback function already defined before it can execute successfully.
```
# Create a callback function for handling the Live Feed output stream data before it gets presented
def live_feed_callback(pom, input_data):
    # Start wth the annotated video frame available from the People Perceptor
    frame = pom.peeps.annotatedFrame().copy()

    # Add some text telling how many people are in the scene
    label = "{} peeps".format(pom.peeps.peopleCount())
    color = (0, 255, 0)
    cv2.putText(frame, str(label), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1, cv2.LINE_AA)

    # If we have anyone, demonstrate looking up that person in the POM by getting their face size
    # And then put it on the frame as some text
    # NOTE: this will just take the face size from the last person in the array
    if pom.peeps.peopleCount() > 0:
        for person_id in pom.peeps.people():
            face_size = pom.peeps.faceSize(person_id)
            face_height = face_size[1]
            label2 = "{} face height".format(face_height)
            color = (0, 255, 255)
            cv2.putText(frame, str(label2), (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1, cv2.LINE_AA)

    # Pass the finished frame out of this callback so the Live Feed output stream can display it
    return frame
    
# Add the Live Feed output stream to the Pipeline and use the callback from above as the handler
pipeline.add_output_stream("output", live_feed_callback, live_feed)
```

## Define an event Output Stream and an input Output Stream and instantiate the People Perceptor

Just like the LiveFeed Output Stream, the People [Perceptor](../terminology/#perceptor) must have the callback already defined before it can work with those callbacks. The input callback simply takes the [Input Stream](../terminology/#input-stream) data and sends it onward to the People [Perceptor](../terminology/#perceptor). The “New Person” event callback simply prints the unique person identifier string to the console output when a new person has been detected by Darcy AI.
```
# Create a callback function for handling the input that is about to pass to the People Perceptor
def people_input_callback(input_data, pom, config):
    # Just take the frame from the incoming Input Stream and send it onward - no need to modify the frame
    frame = input_data.data.copy()
    return frame
    
# Create a callback function for handling the "New Person" event from the People Perceptor
# Just print the person ID to the console
def new_person_callback(person_id):
    print("New person: {}".format(person_id))
    
# Instantiate a People Perceptor
people_ai = PeoplePerceptor()

# Subscribe to the "New Person" event from the People Perceptor and use our callback from above as the handler
people_ai.on("new_person_entered_scene", new_person_callback)
```

## Add the People Perceptor to the Pipeline

```
# Add the People Perceptor instance to the Pipeline and use the input callback from above as the input preparation handler
pipeline.add_perceptor("peeps", people_ai, input_callback=people_input_callback)
```

## Change some configuration items in the People Perceptor

```
# Update the configuration of the People Perceptor to show the pose landmark dots on the annotated video frame
pipeline.set_perceptor_config("peeps", "show_pose_landmark_dots", True)
pipeline.set_perceptor_config("peeps", "pose_landmark_dot_size", 2)
pipeline.set_perceptor_config("peeps", "pose_landmark_dot_color", RGB(0, 255, 0))
```

## Start the Pipeline

```
# Start the Pipeline
pipeline.run()
```

## Check your completed code

Your finished Python file should look similar to this. If it doesn’t, take a minute to figure out what is missing or incorrect. Save your Python file. Next we will run your code!
```
import cv2
import os
import pathlib

from darcyai.perceptor.people_perceptor import PeoplePerceptor
from darcyai.input.camera_stream import CameraStream
from darcyai.output.live_feed_stream import LiveFeedStream
from darcyai.pipeline import Pipeline
from darcyai.config import RGB

# Instantiate an Camera Stream input stream object
camera = CameraStream(video_device=0, fps=20)

# Instantiate the Pipeline object and pass it the Camera Stream object as its input stream source
pipeline = Pipeline(input_stream=camera)

# Create a Live Feed output stream object and specify some URL parameters
live_feed = LiveFeedStream(path="/", port=3456, host="0.0.0.0")

# Create a callback function for handling the Live Feed output stream data before it gets presented
def live_feed_callback(pom, input_data):
    # Start wth the annotated video frame available from the People Perceptor
    frame = pom.peeps.annotatedFrame().copy()

    # Add some text telling how many people are in the scene
    label = "{} peeps".format(pom.peeps.peopleCount())
    color = (0, 255, 0)
    cv2.putText(frame, str(label), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1, cv2.LINE_AA)

    # If we have anyone, demonstrate looking up that person in the POM by getting their face size
    # And then put it on the frame as some text
    # NOTE: this will just take the face size from the last person in the array
    if pom.peeps.peopleCount() > 0:
        for person_id in pom.peeps.people():
            face_size = pom.peeps.faceSize(person_id)
            face_height = face_size[1]
            label2 = "{} face height".format(face_height)
            color = (0, 255, 255)
            cv2.putText(frame, str(label2), (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1, cv2.LINE_AA)

    # Pass the finished frame out of this callback so the Live Feed output stream can display it
    return frame

# Add the Live Feed output stream to the Pipeline and use the callback from above as the handler
pipeline.add_output_stream("output", live_feed_callback, live_feed)

# Create a callback function for handling the input that is about to pass to the People Perceptor
def people_input_callback(input_data, pom, config):
    # Just take the frame from the incoming Input Stream and send it onward - no need to modify the frame
    frame = input_data.data.copy()
    return frame
    
# Create a callback function for handling the "New Person" event from the People Perceptor
# Just print the person ID to the console
def new_person_callback(person_id):
    print("New person: {}".format(person_id))
    
# Instantiate a People Perceptor
people_ai = PeoplePerceptor()

# Subscribe to the "New Person" event from the People Perceptor and use our callback from above as the handler
people_ai.on("new_person_entered_scene", new_person_callback)

# Add the People Perceptor instance to the Pipeline and use the input callback from above as the input preparation handler
pipeline.add_perceptor("peeps", people_ai, input_callback=people_input_callback)

# Update the configuration of the People Perceptor to show the pose landmark dots on the annotated video frame
pipeline.set_perceptor_config("peeps", "show_pose_landmark_dots", True)
pipeline.set_perceptor_config("peeps", "pose_landmark_dot_size", 2)
pipeline.set_perceptor_config("peeps", "pose_landmark_dot_color", RGB(0, 255, 0))

# Start the Pipeline
pipeline.run()
```

## Run your application

Using your IDE, run your Python code. Don't set any breakpoints at first because that will prevent you from seeing the video stream. If you followed the code reference above directly and you have all of the required Python libraries installed, your Darcy AI application should run successfully and stay running until you stop the program execution.

## View your real-time Darcy AI application video output

Once your application is running, you can view the live video feed by visiting the following URL in any browser. The port number 3456 has been specified in the Python code. Feel free to change it and use the alternate port in the URL below.

```
http://localhost:3456/
```

## What you should see

You should see a live video feed coming from your camera. When a person is detected in the field of view, some information should be displayed on the video and some dots should be drawn on top of key face locations. The dots should move with the person's face. This is a demonstration of using Darcy AI to detect the presence of people, assign an anonymous stable identifier to persons as they move around the field of view, and annotate the video frames with text and graphics.

## Now package your Darcy AI application for deployment

Now that your Darcy AI application is working, the next step is to learn how to package it for deployment to a wide range of devices! Follow the [Packaging Guide](../package/) to learn how to package your Darcy AI apps.