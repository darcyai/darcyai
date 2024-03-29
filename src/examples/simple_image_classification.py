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

from darcyai.perceptor.image_classification_perceptor import ImageClassificationPerceptor
from darcyai.perceptor.processor import Processor
from darcyai.input.camera_stream import CameraStream
from darcyai.output.live_feed_stream import LiveFeedStream
from darcyai.pipeline import Pipeline

def perceptor_input_callback(input_data, pom, config):
    return input_data.data


def live_feed_callback(pom, input_data):
    frame = input_data.data.copy()

    if len(pom.image_classification) == 0:
        return frame

    cv2.putText(frame, str(pom.image_classification[0].name), (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    return frame


camera = CameraStream(video_device="/dev/video0", fps=20)

pipeline = Pipeline(input_stream=camera)

live_feed = LiveFeedStream(path="/", port=3456)
pipeline.add_output_stream("output", live_feed_callback, live_feed)

script_dir = pathlib.Path(__file__).parent.absolute()

coral_model_file = os.path.join(script_dir, "models", "coral_mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite")
cpu_model_file = os.path.join(script_dir, "models", "cpu_mobilenet_v2_1.0_224_quant.tflite")

coral_labels_file = os.path.join(script_dir, "models", "inat_bird_labels.txt")
cpu_labels_file = os.path.join(script_dir, "models", "cpu_mobilenet_v2_1.0_224_quant_labels.txt")

image_classification = ImageClassificationPerceptor(processor_preference={
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
                                                    top_k=1,
                                                    quantized=True,
                                                    num_cpu_threads=2)

pipeline.add_perceptor("image_classification", image_classification, input_callback=perceptor_input_callback)

pipeline.run()
