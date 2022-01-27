import cv2
import os
import pathlib

from darcyai.perceptor.coral.object_detection_perceptor import ObjectDetectionPerceptor
from darcyai.input.camera_stream import CameraStream
from darcyai.output.live_feed_stream import LiveFeedStream
from darcyai.pipeline import Pipeline

def perceptor_input_callback(input_data, pom, config):
    return input_data.data


def live_feed_callback(pom, input_data):
    frame = input_data.data.copy()
    if pom.object_detection == None:
        return frame

    for idx, object in enumerate(pom.object_detection[0]):
        bbox = object.bbox
        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
        label = pom.object_detection[1][idx]
        cv2.putText(frame, label, (bbox[0], bbox[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    return frame


camera = CameraStream(video_device="/dev/video0", fps=20)

pipeline = Pipeline(input_stream=camera)

live_feed = LiveFeedStream(path="/", port=3456, host="0.0.0.0")
pipeline.add_output_stream("output", live_feed_callback, live_feed)

script_dir = pathlib.Path(__file__).parent.absolute()
model_file = os.path.join(script_dir, "ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite")
labels_file = os.path.join(script_dir, "coco_labels.txt")
object_detection = ObjectDetectionPerceptor(model_path=model_file, threshold=0.5, labels_file=labels_file)

pipeline.add_perceptor("object_detection", object_detection, accelerator_idx=0, input_callback=perceptor_input_callback)

pipeline.run()
