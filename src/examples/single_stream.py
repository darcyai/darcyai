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

from darcyai.tests.perceptor_mock import PerceptorMock
from darcyai.pipeline import Pipeline
from sample_input_stream import SampleInputStream
from sample_output_stream import SampleOutputStream


class SingleStreamDemo():
    def __init__(self):
        ping = SampleInputStream()
        output_stream = SampleOutputStream()

        self.__pipeline = Pipeline(input_stream=ping,
                                   input_stream_error_handler_callback=self.__input_stream_error_handler_callback,
                                   universal_rest_api=True,
                                   rest_api_base_path="/pipeline",
                                   rest_api_host="0.0.0.0",
                                   rest_api_port=8080)

        self.__pipeline.add_output_stream("output", self.__output_stream_callback, output_stream)

        p1 = PerceptorMock(sleep=0.05)
        self.__pipeline.add_perceptor("p1", p1, accelerator_idx=0, input_callback=self.__perceptor_input_callback)


    def run(self):
        self.__pipeline.run()


    def __perceptor_input_callback(self, input_data, pom, config):
        return input_data


    def __output_stream_callback(self, pom, input_data):
        print(pom.p1)


    def __input_stream_error_handler_callback(self, exception):
        pass


if __name__ == "__main__":
    single_stream = SingleStreamDemo()
    single_stream.run()
