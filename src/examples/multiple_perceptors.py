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

from darcyai.input.camera_stream import CameraStream
from darcyai.pipeline import Pipeline
from darcyai.tests.perceptor_mock import PerceptorMock
from sample_output_stream import SampleOutputStream


class MultiPerceptorDemo():
    def __init__(self):
        camera = CameraStream(video_device="/dev/video0", fps=20)
        output_stream = SampleOutputStream()

        self.__pipeline = Pipeline(input_stream=camera,
                                   num_of_edge_tpus=2,
                                   universal_rest_api=True,
                                   rest_api_base_path="/test",
                                   rest_api_host="0.0.0.0",
                                   rest_api_port=8080)

        self.__pipeline.add_output_stream("output", self.__output_stream_callback, output_stream)

        p1 = PerceptorMock()
        p2 = PerceptorMock()
        p3 = PerceptorMock()
        p11 = PerceptorMock()
        p12 = PerceptorMock()
        p21 = PerceptorMock()
        p121 = PerceptorMock()
        p31 = PerceptorMock()

        #         p1 (0)        p2 (1)     p3 (1)
        #         /  \            |          |
        #    p11 (0) p12 (1)    p21 (0)    p31 (1)
        #               |
        #            p121 (1)
        default_config = {
            "config_1": "value_1",
            "config_2": 2,
        }
        self.__pipeline.add_perceptor("p1", p1, parent=None, multi=False, accelerator_idx=0, input_callback=self.__input_callback, output_callback=self.__output_callback, default_config=default_config)
        self.__pipeline.add_perceptor("p2", p2, parent=None, multi=False, accelerator_idx=1, input_callback=self.__input_callback)
        self.__pipeline.add_perceptor("p3", p3, parent=None, multi=False, accelerator_idx=1, input_callback=self.__input_callback)
        self.__pipeline.add_perceptor("p11", p11, parent="p1", multi=False, accelerator_idx=0, input_callback=self.__input_callback)
        self.__pipeline.add_perceptor("p12", p12, parent="p1", multi=False, accelerator_idx=1, input_callback=self.__input_callback)
        self.__pipeline.add_perceptor("p21", p21, parent="p2", multi=False, accelerator_idx=0, input_callback=self.__input_callback)
        self.__pipeline.add_perceptor("p31", p31, parent="p3", multi=False, accelerator_idx=1, input_callback=self.__input_callback)
        self.__pipeline.add_perceptor("p121", p121, parent="p12", multi=False, accelerator_idx=1, input_callback=self.__input_callback)

        self.__pipeline.set_perceptor_config("p1", "config_3", True)

        p1.on("event_1", self.__output_callback)


    def run(self):
        self.__pipeline.run()


    def __input_callback(self, data, pom, config):
        return data


    def __output_callback(self, data, pom):
        return data


    def __output_stream_callback(self, pom, input_data):
        pass


if __name__ == "__main__":
    demo = MultiPerceptorDemo()
    demo.run()
