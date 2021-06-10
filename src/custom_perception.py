from darcyai import DarcyAI


def analyze(frame_number, objects):
    pass
    # for object in objects:
    #     print("{}: {}".format(object.label_id, object.score))


if __name__ == "__main__":
    ai = DarcyAI(
        data_processor=analyze,
        custom_perception_model="src/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite")
    ai.Start()
