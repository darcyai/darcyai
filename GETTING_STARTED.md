# Getting started with Darcy AI

The Darcy AI SDK offers a rich set of features that Darcy AI application developers can use to easily build complex AI processing chains. This makes developing rich real-time applications possible in a shorter timeframe and with a much more standardized approach.

If you have not yet read the overview of Darcy AI terminology, it is recommended that you do that first. You can find it here [Darcy AI Terminology Guide](../terminology/).

## Thinking in terms of Darcy AI pipelines

The concept of an AI [Pipeline](../terminology/#pipeline) is similar to complex event processing (CEP) and data stream processing, but there are some unique aspects you will notice when building with the Darcy AI.

You are allowed only one Darcy AI pipeline in your application. There is a reason for this. A pipeline allows you to order the AI operations in a way that produces predictable trade-offs. One example is placing two different AI operations in parallel. On a hardware system that does not have enough AI accelerator hardware, Darcy will need to make a decision about how to run those operations. If you had more than one pipeline, Darcy would have conflicting intelligence about how to sequence the operations and you would be unable to predict which pipeline would be able to process.

You should consider a pipeline to be the backbone of your application flow. You only want one backbone and it should include all of the AI processing that you need in order to make your application run smoothly.

The way you structure the pipeline will have an effect on AI processing speed and timing reliability. For processes that must occur in a straight line, attach processing steps called Perceptors one after the other. For processes that can take place in any order and do not depend on one another, you can use parallel ordering.

A Darcy AI pipeline is a data graph and can be modeled visually like a sequence tree.
```
         p1 (0)        p2 (1)     p3 (1)
         /  \            |          |
    p11 (0) p12 (1)    p21 (0)    p31 (1)
               |
            p121 (1)
```

## Full trips through the pipeline are your application "main loop"

Every application has a main processing loop that defines the code structure. Everything is built around that main loop and often gets triggered as part of the main loop’s operations. For your Darcy AI application, you should think of each full trip through the pipeline as one iteration of your main loop. This means you should include all of the AI processing steps that you want to happen every time in your pipeline. Processing steps that should only take place on certain conditions may be best implemented as immediate AI processing (see below) so Darcy does not use precious resources for processing that you don’t want.

## Start with an Input Stream

The first stage of every pipeline cycle (also called a [frame or pulse](../terminology/#frame-cycle-or-pulse)) is the unprocessed data coming from the [Input Stream](../terminology/#input-stream) that you have chosen for your application. Choose an Input Stream that provides the sensor data that you want Darcy to process. This may be audio, video, LiDAR, thermal video, or just about anything you can imagine.

A good example of an Input Stream is the CameraStream class that comes built-in with the Darcy AI SDK. This Input Stream allows you to specify the device path for a video camera. It will read the video camera feed and bring it into Darcy at the frame rate and resolution you specify.

Instantiate the CameraStream object and set some of its parameters like this:
```
from darcyai.input.camera_stream import CameraStream

camera = CameraStream(video_device="/dev/video0", fps=20)
```

## Attach a Perceptor

The main processing of the Darcy AI Pipeline is found in the [Perceptors](../terminology/#perceptor). Adding a Perceptor is easy. You just instantiate the Perceptor class, perform any initial operations to set it up, and then add it to the Pipeline in whatever position you desire. Each Perceptor offers different configuration options and produces different results. Perceptors also offer events to which you can subscribe.

A good example of a powerful Perceptor is the People Perceptor that is built-in with the Darcy AI SDK. This Perceptor is focused on detecting and processing people so you, as the developer, can simply work with semantic data results.

Here is an example of creating a People Perceptor instance and adding it to the Pipeline:
```
from darcyai.perceptor.coral.people_perceptor import PeoplePerceptor

people_ai = PeoplePerceptor()
pipeline.add_perceptor("mypeople", people_ai, input_callback=people_input_callback)
```

## Every pipeline step stores data in the Perception Object Model (POM)

When a Perceptor has executed, its results are added to the [Perception Object Model (POM)](../terminology/#perception-object-model-pom) and the Pipeline continues to the next Perceptor or [Output Stream](../terminology/#output-stream) if there are not further Perceptors in the Pipeline. The POM is like a shopping cart that gets loaded with data as it moves along. Everything is categorized in the POM so you can easily access the data associated with any Perceptor. The reference is the name you gave that Perceptor when adding it to the Pipeline.

Every Perceptor produces its own specific data structure and may also provide convenience functions for performing operations on the result data, such as retrieving a particular person from a set or grabbing the face image of a specific person. The data structure and set of convenience functions for each Perceptor can be found in the documentation for that Perceptor.

Here is an example of a [callback](../terminology/#callback) that is taking advantage of several powerful convenience functions in the POM under the results of the People Perceptor named as “mypeople”:
```
def my_callback(pom, input_data):
  current_display_frame = pom.mypeople.annotatedFrame().copy()
  all_people = pom.mypeople.people()
  current_number_of_people = pom.mypeople.peopleCount()
```

## Using Output Streams

The last stage of every pipeline cycle is the set of Output Streams that you have added to the pipeline. Any number of Output Streams can be added, giving you the power to put data in many places or perform complex operations such as storing it locally, sending it upstream to a cloud environment, and also displaying a UI at the same time. Output Streams provide a callback which allows you, as the developer, to prepare the data that will be processed by the Output Stream. This is very useful if you want to format data before sending upstream, filter data before storing it on disk, or edit a video frame before you display it.

A good example of an Output Stream is the LiveFeedStream class that comes built-in with the Darcy AI SDK. This Output Stream allows you to configure network host and port information and it will open a video feed that you can view with any web browser.

Instantiate the LiveFeed output stream object and set some of its parameters like this:
```
from darcyai.output.live_feed_stream import LiveFeedStream

def live_feed_callback(pom, input_data):
    #Start wth the annotated video frame available from the People Perceptor
    frame = pom.mypeople.annotatedFrame().copy()

    #Add some text telling how many people are in the scene
    label = "{} people".format(pom.mypeople.peopleCount())
    color = (0, 255, 0)
    cv2.putText(frame, str(label), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1, cv2.LINE_AA)

    #Pass the finished frame out of this callback so the Live Feed output stream can display it
    return frame

live_feed = LiveFeedStream(path="/", port=3456, host="0.0.0.0")
pipeline.add_output_stream("output", live_feed_callback, live_feed)
```

## The Perceptor input and output callbacks

Every Perceptor that is added to the Pipeline provides both an input callback and output callback. The input callback is available for you, as the developer, to prepare the data that will be passed to the perceptor. The input callback signature is any function that accepts three parameters. The parameters are an input data object, POM object, and configuration object. Pass your input callback function as a parameter when you add the Perceptor to the Pipeline.
```
def people_perceptor_input_callback(input_data, pom, config):
    #Just take the frame from the incoming Input Stream and send it onward - no need to modify the frame
    frame = input_data.data.copy()
    return frame
    
people_ai = PeoplePerceptor()
pipeline.add_perceptor("mypeople", people_ai, input_callback=people_perceptor_input_callback)
```

The output callback is intended for you to perform filtering, refinement, editing, and any other data operations on the output of the Perceptor before Darcy moves further down the Pipeline. In many cases, you will not have a need to use this callback. The output of the Perceptor will be usable in its original form. One example of a good use of the output callback, though, is to remove data from the POM that does not fit certain business criteria, such as deleting people from the POM who are facing the wrong direction. Usage of the output callback is similar to the input callback.
```
def people_perceptor_output_callback(perceptor_input, pom, config):
    #Just take the last person from the results
    all_people = pom.mypeople.people()
    filtered_data = None
    for person in all_people:
      filtered_data = person
    return filtered_data
    
people_ai = PeoplePerceptor()
pipeline.add_perceptor("mypeople", people_ai, output_callback=people_perceptor_output_callback)
```

## Configuring Perceptors and Output Streams

There are two ways to configure the Perceptors and Output Streams in the Darcy AI system. One approach is to set the configuration in code. The other approach is to use the configuration REST API that becomes available when your Darcy AI application is running. Both approaches also provide the ability for you to fetch the current configuration of both Perceptors and Output Streams.

To retrieve the current configuration of a Perceptor or Output Stream in code, call the correct method on the Pipeline object.
```
perceptor_config_dictionary = pipeline.get_perceptor_config("mypeople")
outstream_config_dictionary = pipeline.get_output_stream_config("videoout")
```

To set a configuration item in code, call the pipeline method and pass the name of the configuration item as a string and also pass the new value. The list of configuration items will be provided in the Perceptor or Output Stream documentation, along with accepted types of values.
```
pipeline.set_perceptor_config("mypeople", "show_pose_landmark_dots", True)
```

To retrieve the current configuration using the REST API, use the following URIs and fill in your device hostname or IP address and replace the Perceptor or Output Stream name with the name you have chosen when adding it to the pipeline.
```
GET http://HOSTNAME_OR_IP:8080/pipeline/perceptors/PERCEPTOR_NAME/config
GET http://HOSTNAME_OR_IP:8080/pipeline/outputs/OUTPUT_STREAM/config
```

And to use the REST API to make changes, pass your updated configuration JSON to the following URIs as a PATCH request.
```
PATCH http://HOSTNAME_OR_IP:8080/pipeline/perceptors/PERCEPTOR_NAME/config
PATCH http://HOSTNAME_OR_IP:8080/pipeline/outputs/OUTPUT_STREAM/config
```

## Subscribing to Perceptor events

Perceptors may provide events to which you can subscribe with a callback function. The list of events that a Perceptor provides will be listed in the documentation for that specific Perceptor. To subscribe to an event you pass a callback function with the proper number of parameters as listed in the documentation for that event. Use the `.on()` method of a Perceptor to subscribe and pass the event name as a string.
```
def new_person_callback(person_id):
    print(person_id)

people_ai = PeoplePerceptor()
people_ai.on("new_person_entered_scene", new_person_callback)
```

## Immediate and conditional AI processing

While the Darcy AI Pipeline is intended for executing AI processing against all incoming data, there are times when you may want to run an AI process against arbitrary data immediately. You may also want to selectively run an AI process under certain conditions but not others.

The Pipeline object provides a method for executing a Perceptor against arbitrary data. You can use any Perceptor. The data you pass must be in the form of a StreamData object, which means that you can put any data in the object but you must also add an integer timestamp.
```
people_ai = PeoplePerceptor()
current_time = int(time.time())
my_data = StreamData(saved_video_frame, current_time)
pipeline.run_perceptor(people_ai, my_data)
```

## Bring it all together with a full application

The best way to learn all of these concepts is to see them in action. Start with building a sample application that illustrates all of these topics in actual code. Then build your own! You can find a sample application guide here [Build Guide](../build/).
