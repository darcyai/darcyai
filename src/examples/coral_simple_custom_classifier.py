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

from darcyai.perceptor.coral.image_classification_perceptor import ImageClassificationPerceptor
from darcyai.input.camera_stream import CameraStream
from darcyai.output.live_feed_stream import LiveFeedStream
from darcyai.pipeline import Pipeline

def mask_check_input_callback(input_data, pom, config):
    frame = input_data.data.copy()
    crop_face = frame[200:280, 280:360]
    color_cvt_face = cv2.cvtColor(crop_face, cv2.COLOR_BGR2RGB)

    return color_cvt_face


def live_feed_callback(pom, input_data):
    frame = input_data.data.copy()

    if len(pom.mask_check[1]) > 0:
        label = pom.mask_check[1][0]
    else:
        label = "No Mask"

    color = (0, 255, 0) if label == "Mask" else (0, 0, 255)
    cv2.rectangle(frame, (270, 180), (370, 300), color, 2)
    cv2.putText(frame, str(label), (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    return frame


camera = CameraStream(video_device="/dev/video0", fps=20)

pipeline = Pipeline(input_stream=camera)

live_feed = LiveFeedStream(path="/", port=3456, host="0.0.0.0")
pipeline.add_output_stream("output", live_feed_callback, live_feed)

script_dir = pathlib.Path(__file__).parent.absolute()
model_file = os.path.join(script_dir, "models", "face_mask_detection.tflite")
labels = {
    0: "No Mask",
    1: "Mask",
}
image_classification = ImageClassificationPerceptor(model_path=model_file, threshold=0.85, top_k=1, labels=labels)

pipeline.add_perceptor("mask_check", image_classification, input_callback=mask_check_input_callback)

pipeline.run()
