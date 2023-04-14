# Copyright 2022 Edgeworx, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import cv2
import os
import pathlib

from darcyai.perceptor.object_detection_perceptor import ObjectDetectionPerceptor
from darcyai.perceptor.processor import Processor
from darcyai.input.camera_stream import CameraStream
from darcyai.output.live_feed_stream import LiveFeedStream
from darcyai.pipeline import Pipeline

def perceptor_input_callback(input_data, pom, config):
    return input_data.data


def live_feed_callback(pom, input_data):
    frame = input_data.data.copy()
    if pom.object_detection == None:
        return frame

    for object in pom.object_detection:
        cv2.rectangle(frame, (object.xmin, object.ymin), (object.xmax, object.ymax), (0, 255, 0), 2)
        cv2.putText(frame, object.name, (object.xmin, object.ymin - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    return frame


camera = CameraStream(video_device="/dev/video0", fps=20)

pipeline = Pipeline(input_stream=camera)

live_feed = LiveFeedStream(path="/", port=3456)
pipeline.add_output_stream("output", live_feed_callback, live_feed)

script_dir = pathlib.Path(__file__).parent.absolute()

coral_model_file = os.path.join(script_dir, "models", "coral_ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite")
coral_labels_file = os.path.join(script_dir, "models", "coco_labels.txt")

cpu_model_file = os.path.join(script_dir, "models", "cpu_coco_ssd_mobilenet.tflite")
cpu_labels_file = os.path.join(script_dir, "models", "coco_labels.txt")

object_detection = ObjectDetectionPerceptor(processor_preference={
                                                Processor.CORAL_EDGE_TPU: {
                                                    "model_path": coral_model_file,
                                                    "labels_file": coral_labels_file,
                                                },
                                                Processor.CPU: {
                                                    "model_path": cpu_model_file,
                                                    "labels_file": cpu_labels_file,
                                                },
                                            },
                                            threshold=0.5,
                                            quantized=False,
                                            num_cpu_threads=2)

pipeline.add_perceptor("object_detection", object_detection, accelerator_idx=0, input_callback=perceptor_input_callback)

pipeline.run()
