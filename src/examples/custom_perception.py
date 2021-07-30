import cv2
from darcyai import DarcyAI


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


if __name__ == "__main__":
    ai = DarcyAI(
        data_processor=analyze,
        frame_processor=frame_processor,
        detect_perception_model="src/examples/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite",
        detect_perception_threshold=0.8,
        detect_perception_labels_file="src/examples/coco_labels.txt")
    ai.Start()
