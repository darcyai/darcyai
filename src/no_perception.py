import cv2
import threading
import time
from darcyai import DarcyAI


if __name__ == "__main__":
    ai = DarcyAI(do_perception=False)

    threading.Thread(target=ai.Start).start()

    ai.LoadCustomModel('src/qrcode_detection.tflite')

    while True:
        time.sleep(1)

        _, latest_frame = ai.GetLatestFrame()
        result = ai.RunCustomModel(latest_frame)
