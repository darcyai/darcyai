import cv2
import os
import threading
from darcyai import DarcyAI
from flask import Flask, request, Response


VIDEO_DEVICE = os.getenv("VIDEO_DEVICE", "/dev/video0")
THRESHOLD = float(os.getenv("THRESHOLD", "0.7"))


def analyze(frame_number, objects, labels):
    for idx, object in enumerate(objects):
        print("%s: %.1f%%" % (labels[idx], object.score * 100))


def draw_object_rectangle_on_frame(frame, object, label):
    box = object.bbox
    cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 0, 255), 1)
    cv2.putText(frame, "%s: %.1f%%" % (label, object.score * 100), (box[0] + 2, box[1] + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    return frame


def frame_processor(frame_number, frame, detected_objects, labels):
    frame_clone = frame.copy()
    for idx, object in enumerate(detected_objects):
        frame_clone = draw_object_rectangle_on_frame(frame_clone, object, labels[idx])

    return frame_clone


def root():
    return flask_app.send_static_file('index.html')


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.realpath(__file__))
    flask_app = Flask(__name__, static_url_path=script_dir)
    flask_app.add_url_rule("/", "root", root)
    
    ai = DarcyAI(
        data_processor=analyze,
        frame_processor=frame_processor,
        flask_app=flask_app,
        detect_perception_model="ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite",
        detect_perception_threshold=THRESHOLD,
        detect_perception_labels_file="coco_labels.txt",
        use_pi_camera=False,
        video_device=VIDEO_DEVICE)
    threading.Thread(target=ai.Start).start()

    flask_app.run(
        host="0.0.0.0",
        port=3456,
        debug=False)
