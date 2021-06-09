import cv2
from darcyai import DarcyAI


def analyze(frame_number, objects):
    for object in objects:
        if object.body["has_face"]:
            print("{}: {}".format(object.object_id, object.body["face_position"]))
        else:
            print("{}: No face".format(object.object_id))


def draw_object_rectangle_on_frame(frame, object):
    box = object.bounding_box
    cv2.rectangle(frame, box[0], box[1], (0, 0, 255), 1)
    cv2.putText(frame, "{}: {}".format(object.object_id, object.body["face_position"]), (box[0][0] + 2, box[0][1] + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    return frame


def frame_processor(frame_number, frame, detected_objects):
    frame_clone = frame.copy()
    for object in detected_objects:
        frame_clone = draw_object_rectangle_on_frame(frame_clone, object)

    return frame_clone


if __name__ == "__main__":
    ai = DarcyAI(data_processor=analyze, frame_processor=frame_processor)
    ai.Start()
