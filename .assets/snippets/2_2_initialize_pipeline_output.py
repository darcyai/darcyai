# Instantiate the Pipeline object and pass it the Camera Stream object as its input stream source
pipeline = Pipeline(input_stream=camera)

# Create a Live Feed output stream object and specify some URL parameters
live_feed = LiveFeedStream(path="/", port=3456, host="0.0.0.0")