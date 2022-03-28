# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

import platform

from darcyai.input.camera_stream import CameraStream
from darcyai.output.live_feed_stream import LiveFeedStream
from darcyai.tests.perceptor_mock import PerceptorMock
from darcyai.pipeline import Pipeline


def perceptor_input_callback(input_data, pom, config):
    return input_data


def output_callback(pom, input_data):
    return input_data.data


camera = CameraStream(video_device=0 if platform.system() == "Darwin" else "/dev/video0", fps=20)
output_stream = LiveFeedStream(port=3456, host="0.0.0.0", path="/live-stream")

pipeline = Pipeline(input_stream=camera,
                    num_of_edge_tpus=2,
                    universal_rest_api=True,
                    rest_api_base_path="/test",
                    rest_api_host="0.0.0.0",
                    rest_api_port=8080)

pipeline.add_output_stream("live_stream", output_callback, output_stream)

p1 = PerceptorMock(sleep=0.05)
pipeline.add_perceptor("p1", p1, accelerator_idx=0, input_callback=perceptor_input_callback)

pipeline.run()
