import cv2
import os
import queue
import threading
import time
from darcyai import DarcyAI


in_queue = queue.Queue()
seen_persons = []


def worker(in_q):
  batch_list = []
  while True:
    milltime, object = in_q.get()
    batch_list.append((milltime, object))

    if len(batch_list) < 50:
      continue

    try:
      save_data(batch_list)
    except:
      pass
    finally:
      batch_list = []


def get_csv(data, only_first_times=False):
  header = "timestamp,uuid,face_direction\n"
  content = ""
  for item in data:
    content += "{},{},{}\n".format(item[0], item[1].uuid, item[1].body["face_position"])

  return header, content


def save_data(data):
  filename = "data.csv"
  header, content = get_csv(data)
  
  if os.path.isfile(filename):
    header = None

  with open(filename, 'a') as f:
    if not header is None:
      f.write(header)
    f.write(content)


def analyze(in_q):
  def analyze_helper(frame_number, objects):
    for object in objects:
      if object.body["has_face"] and object.uuid is not None:
        in_q.put((int(time.time() * 1000), object))

  return analyze_helper


def draw_object_rectangle_on_frame(frame, object):
  box = object.bounding_box
  cv2.rectangle(frame, box[0], box[1], (0, 0, 255), 1)
  cv2.putText(frame, "{}: {}".format(object.uuid, object.body["face_position"]), (box[0][0] + 2, box[0][1] + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

  return frame


def frame_processor(frame_number, frame, detected_objects):
  frame_clone = frame.copy()
  for object in detected_objects:
    frame_clone = draw_object_rectangle_on_frame(frame_clone, object)

  return frame_clone


if __name__ == "__main__":
  work_thread = threading.Thread(target=worker, args=[in_queue])
  work_thread.start()

  ai = DarcyAI(data_processor=analyze(in_queue), frame_processor=frame_processor)
  ai.Start()
