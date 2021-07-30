import threading
import time
from darcyai import DarcyAI


if __name__ == "__main__":
    ai = DarcyAI(do_perception=False)

    threading.Thread(target=ai.Start).start()

    ai.LoadCustomModel('src/examples/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite')

    while True:
        time.sleep(1)

        _, latest_frame = ai.GetLatestFrame()
        latency, result = ai.RunCustomModel(latest_frame)
