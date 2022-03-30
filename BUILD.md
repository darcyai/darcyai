# Building your Darcy AI application

It’s easy to build a Darcy AI application but how do you get started? Here’s an example application that introduces all of the main concepts you will need for building your own application. Start by following along!

## Requirements

You’ll need to have a few things in place before you build. Here’s the list:
- Visual Studio Code (VS Code) with Python extensions
	- [https://code.visualstudio.com/](https://code.visualstudio.com/)
	- [https://marketplace.visualstudio.com/items?itemName=ms-python.python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- A Raspberry Pi with an attached video camera and Google Coral edge TPU
- Set up your VS Code environment to develop on your Raspberry Pi remotely
	- [https://www.raspberrypi.com/news/coding-on-raspberry-pi-remotely-with-visual-studio-code/](https://www.raspberrypi.com/news/coding-on-raspberry-pi-remotely-with-visual-studio-code/)
- Python 3.5+
- Docker on your Raspberry Pi

## Environment setup

To check if your Raspberry Pi meets all of the requirements for building and debugging Darcy AI applications, run the system check script [check.bash](https://github.com/darcyai/darcyai-sdk/blob/master/check.bash).

If you need to setup your Raspberry Pi as a Darcy AI development environment, follow the [Raspberry Pi Environment Setup Guide](/raspberry-pi-setup/).

## Create your application Python file and import libraries

You only need a single Python file to build a Darcy AI application. Open a new .py file in VS Code and name it whatever you want. Then add the following statements at the top to include the Darcy AI libraries and some additional helpful libraries:
```
import cv2
import os
import pathlib

from darcyai.perceptor.coral.people_perceptor import PeoplePerceptor
from darcyai.input.camera_stream import CameraStream
from darcyai.output.live_feed_stream import LiveFeedStream
from darcyai.pipeline import Pipeline
```

If you don’t have the `darcyai` library installed yet, you can install it with PIP package installer for Python using the following commands, which you should run both on your development workstation and on your Raspberry Pi where you will be running your application:
```
pip install darcyai
```

If you have multiple versions of Python on your system, you may need to install the `darcyai` library using the Python3 version of PIP as follows:
```
pip3 install darcyai
```

## Add the Pipeline, Input Stream, and Output Stream objects

This part is quite easy. Just follow the comments to learn more about these 3 important lines of code.
```
#Instantiate an Camera Stream input stream object
camera = CameraStream(video_device="/dev/video0", fps=20)

#Instantiate the Pipeline object and pass it the Camera Stream object as its input stream source
pipeline = Pipeline(input_stream=camera)

#Create a Live Feed output stream object and specify some URL parameters
live_feed = LiveFeedStream(path="/", port=3456, host="0.0.0.0")
```

## Set up a callback and add the Output Stream to the Pipeline

Before we add the LiveFeed Output Stream to the Pipeline, we need to set up a callback function that we are going to use to process the data before displaying the video. Follow the comments to learn about the steps that are taken. This is the most complex portion of the whole application and it is where all of the business logic is taking place. After the callback function definition, there is a line for adding the LiveFeed Output Stream to the Pipeline. That command needs to have the callback function already defined before it can execute successfully.
```
#Create a callback function for handling the Live Feed output stream data before it gets presented
def live_feed_callback(pom, input_data):
    #Start wth the annotated video frame available from the People Perceptor
    frame = pom.peeps.annotatedFrame().copy()

    #Add some text telling how many people are in the scene
    label = "{} peeps".format(pom.peeps.peopleCount())
    color = (0, 255, 0)
    cv2.putText(frame, str(label), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1, cv2.LINE_AA)

    #If we have anyone, demonstrate looking up that person in the POM by getting their face size
    #And then put it on the frame as some text
    #NOTE: this will just take the face size from the last person in the array
    if pom.peeps.peopleCount() > 0:
        for person_id in pom.peeps.people():
            face_size = pom.peeps.faceSize(person_id)
            face_height = face_size[1]
            label2 = "{} face height".format(face_height)
            color = (0, 255, 255)
            cv2.putText(frame, str(label2), (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1, cv2.LINE_AA)

    #Pass the finished frame out of this callback so the Live Feed output stream can display it
    return frame
    
#Add the Live Feed output stream to the Pipeline and use the callback from above as the handler
pipeline.add_output_stream("output", live_feed_callback, live_feed)
```

## Define an event callback and an input callback and instantiate the People Perceptor

Just like the LiveFeed Output Stream, the People Perceptor must have the callbacks already defined before it can work with those callbacks. The input callback simply takes the Input Stream data and sends it onward to the People Perceptor. The “New Person” event callback simply prints the unique person identifier string to the console output when a new person has been detected by Darcy.
```
#Create a callback function for handling the input that is about to pass to the People Perceptor
def people_input_callback(input_data, pom, config):
    #Just take the frame from the incoming Input Stream and send it onward - no need to modify the frame
    frame = input_data.data.copy()
    return frame
    
#Create a callback function for handling the "New Person" event from the People Perceptor
#Just print the person ID to the console
def new_person_callback(person_id):
    print("New person: {}".format(person_id))
    
#Instantiate a People Perceptor
people_ai = PeoplePerceptor()

#Subscribe to the "New Person" event from the People Perceptor and use our callback from above as the handler
people_ai.on("new_person_entered_scene", new_person_callback)
```

## Add the People Perceptor to the Pipeline

```
#Add the People Perceptor instance to the Pipeline and use the input callback from above as the input preparation handler
pipeline.add_perceptor("peeps", people_ai, input_callback=people_input_callback)
```

## Change some configuration items in the People Perceptor

```
#Update the configuration of the People Perceptor to show the pose landmark dots on the annotated video frame
pipeline.set_perceptor_config("peeps", "show_pose_landmark_dots", True)
pipeline.set_perceptor_config("peeps", "pose_landmark_dot_size", 2)
pipeline.set_perceptor_config("peeps", "pose_landmark_dot_color", "0,255,0")
```

## Start the Pipeline

```
#Start the Pipeline
pipeline.run()
```

## Check your completed code

Your finished Python file should look similar to this. If it doesn’t, take a minute to figure out what is missing or incorrect. Next we will build an application container from this code.
```
import cv2
import os
import pathlib

from darcyai.perceptor.coral.people_perceptor import PeoplePerceptor
from darcyai.input.camera_stream import CameraStream
from darcyai.output.live_feed_stream import LiveFeedStream
from darcyai.pipeline import Pipeline

#Instantiate an Camera Stream input stream object
camera = CameraStream(video_device="/dev/video0", fps=20)

#Instantiate the Pipeline object and pass it the Camera Stream object as its input stream source
pipeline = Pipeline(input_stream=camera)

#Create a Live Feed output stream object and specify some URL parameters
live_feed = LiveFeedStream(path="/", port=3456, host="0.0.0.0")

#Create a callback function for handling the Live Feed output stream data before it gets presented
def live_feed_callback(pom, input_data):
    #Start wth the annotated video frame available from the People Perceptor
    frame = pom.peeps.annotatedFrame().copy()

    #Add some text telling how many people are in the scene
    label = "{} peeps".format(pom.peeps.peopleCount())
    color = (0, 255, 0)
    cv2.putText(frame, str(label), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1, cv2.LINE_AA)

    #If we have anyone, demonstrate looking up that person in the POM by getting their face size
    #And then put it on the frame as some text
    #NOTE: this will just take the face size from the last person in the array
    if pom.peeps.peopleCount() > 0:
        for person_id in pom.peeps.people():
            face_size = pom.peeps.faceSize(person_id)
            face_height = face_size[1]
            label2 = "{} face height".format(face_height)
            color = (0, 255, 255)
            cv2.putText(frame, str(label2), (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1, cv2.LINE_AA)

    #Pass the finished frame out of this callback so the Live Feed output stream can display it
    return frame

#Add the Live Feed output stream to the Pipeline and use the callback from above as the handler
pipeline.add_output_stream("output", live_feed_callback, live_feed)

#Create a callback function for handling the input that is about to pass to the People Perceptor
def people_input_callback(input_data, pom, config):
    #Just take the frame from the incoming Input Stream and send it onward - no need to modify the frame
    frame = input_data.data.copy()
    return frame
    
#Create a callback function for handling the "New Person" event from the People Perceptor
#Just print the person ID to the console
def new_person_callback(person_id):
    print("New person: {}".format(person_id))
    
#Instantiate a People Perceptor
people_ai = PeoplePerceptor()

#Subscribe to the "New Person" event from the People Perceptor and use our callback from above as the handler
people_ai.on("new_person_entered_scene", new_person_callback)

#Add the People Perceptor instance to the Pipeline and use the input callback from above as the input preparation handler
pipeline.add_perceptor("peeps", people_ai, input_callback=people_input_callback)

#Update the configuration of the People Perceptor to show the pose landmark dots on the annotated video frame
pipeline.set_perceptor_config("peeps", "show_pose_landmark_dots", True)
pipeline.set_perceptor_config("peeps", "pose_landmark_dot_size", 2)
pipeline.set_perceptor_config("peeps", "pose_landmark_dot_color", "0,255,0")

#Start the Pipeline
pipeline.run()
```

## Save your Python file to your Raspberry Pi

If you are using VS Code remote development, then your file should automatically save on the device when you save in VS Code. If you are manually adding your file to your Raspberry Pi, copy the file to the device now.

## Add a Dockerfile to the same directory as your Python file

You will build a Docker container to run your Darcy AI application. You only need your Python file and a Dockerfile to build the container. Make sure you create this Dockerfile in the same directory as your Python file and change the name from YOURFILE.py to the actual name of your file.
```
FROM darcyai/darcy-ai-coral:dev

RUN python3 -m pip install --upgrade darcyai

COPY YOURFILE.py /src/my_app.py

ENTRYPOINT ["/bin/bash", "-c", "cd /src/ && python3 -u ./my_app.py"]
```

## Build your Docker container

Use the following command to build your Docker container. It may take 10 or 15 minutes if you are building for the first time and you do not have a very fast internet connection. This is because the underlying container base images will need to be downloaded. After the first build, this process should only take a minute or two.
```
sudo docker build -t darcydev/my-people-ai-app:1.0.0 .
```

## Run your application

Use this Docker command to run your application container right away. You can also use this Docker container with the [Darcy Cloud](https://cloud.darcy.ai) to deploy and manage the application.
```
sudo docker run -d --privileged --net=host -p 3456:3456 -p 8080:8080 -v /dev:/dev darcydev/my-people-ai-app:1.0.0
```

## View your real-time Darcy AI application video output

Once your application container is running, you can view the live video feed by visiting the following URL in any browser. Replace `YOUR.DEVICE.IP.ADDRESS` with the actual IP address of your Raspberry Pi.
```
https://YOUR.DEVICE.IP.ADDRESS:3456/
```